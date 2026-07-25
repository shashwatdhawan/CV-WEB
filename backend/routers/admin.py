import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from backend.database import get_db
from backend.dependencies import get_or_create_current_user, require_admin
from backend.models import AdminInvitationCode, AuditLog, Coupon, Feedback, Order, Product, User
from backend.schemas import AdminInviteCreateRequest, AdminInviteRedeemRequest, CouponCreateRequest, StatusUpdateRequest
from backend.services.audit import log_action
from backend.services.admin_codes import hash_code, redeem_admin_code
from backend.services.coupons import normalize_code, serialize_coupon
from backend.services.orders import serialize_order, update_order_status
from backend.routers.feedback import serialize_feedback


router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    if not request.app.state.current_user(request):
        return RedirectResponse("/login")
    try:
        require_admin(request, db)
    except HTTPException:
        return RedirectResponse("/")
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "admin.html")


@router.get("/api/admin/overview")
async def api_admin_overview(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    admin = require_admin(request, db)
    data = {
        "totalUsers": db.query(User).count(),
        "totalProducts": db.query(Product).count(),
        "pendingOrders": db.query(Order).filter(Order.status.in_(["pending", "awaiting_staff"])).count(),
        "completedOrders": db.query(Order).filter(Order.status == "completed").count(),
        "revenue": sum(row.final_total for row in db.query(Order).filter(Order.status.in_(["paid", "processing", "completed"])).all()),
        "coupons": db.query(Coupon).count(),
        "admins": db.query(User).filter(User.is_admin.is_(True)).count(),
        "recentActivity": [
            {"action": log.action, "details": log.details, "createdAt": log.created_at.isoformat() if log.created_at else None}
            for log in db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
        ],
    }
    return JSONResponse(data)


@router.post("/api/admin/bootstrap")
async def api_admin_bootstrap(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    if db.query(User).filter(User.is_admin.is_(True)).count() > 0:
        raise HTTPException(status_code=403, detail="Admin bootstrap is already disabled because an admin exists.")
    user = get_or_create_current_user(request, db)
    user.is_admin = True
    db.commit()
    log_action(db, user, "Admin Bootstrapped", "user", user.id, "First admin created.")
    return JSONResponse({"ok": True, "message": "You are now the first admin."})


@router.get("/api/admin/orders")
async def api_admin_orders(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    require_admin(request, db)
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(200).all()
    return JSONResponse([serialize_order(order) for order in orders])


@router.put("/api/admin/orders/{order_number}/status")
async def api_admin_update_order_status(order_number: str, payload: StatusUpdateRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    admin = require_admin(request, db)
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    try:
        order = update_order_status(db, order, payload.status, admin, payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_action(db, admin, "Order Status Changed", "order", order.order_number, f"Changed to {payload.status}. {payload.note}")
    return JSONResponse(serialize_order(order))


@router.get("/api/admin/coupons")
async def api_admin_coupons(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    require_admin(request, db)
    return JSONResponse([serialize_coupon(coupon) for coupon in db.query(Coupon).order_by(Coupon.created_at.desc()).all()])


@router.post("/api/admin/coupons")
async def api_admin_create_coupon(payload: CouponCreateRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    admin = require_admin(request, db)
    code = normalize_code(payload.code)
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=400, detail="Coupon already exists.")
    coupon = Coupon(
        code=code,
        label=payload.label,
        coupon_type=payload.coupon_type,
        value=payload.value,
        enabled=payload.enabled,
        minimum_purchase=payload.minimum_purchase,
        max_uses=payload.max_uses,
        max_uses_per_user=payload.max_uses_per_user,
        applicable_products="\n".join(payload.applicable_products),
        applicable_categories="\n".join(payload.applicable_categories),
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    log_action(db, admin, "Coupon Created", "coupon", coupon.code, coupon.label)
    return JSONResponse(serialize_coupon(coupon))


@router.post("/api/admin/invites")
async def api_admin_create_invite(payload: AdminInviteCreateRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    admin = require_admin(request, db)
    code = f"CVADMIN-{secrets.token_urlsafe(24)}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours) if payload.expires_in_hours else None
    invite = AdminInvitationCode(code_hash=hash_code(code), code_preview=code[:16], expires_at=expires_at, created_by_user_id=admin.id)
    db.add(invite)
    db.commit()
    log_action(db, admin, "Admin Invite Created", "admin_invite", invite.id, invite.code_preview)
    return JSONResponse({"code": code, "expiresAt": expires_at.isoformat() if expires_at else None})


@router.post("/api/admin/invites/redeem")
async def api_admin_redeem_invite(payload: AdminInviteRedeemRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    user = get_or_create_current_user(request, db)
    try:
        message = redeem_admin_code(db, user, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse({"ok": True, "message": message})


@router.get("/api/admin/feedback")
async def api_admin_feedback(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    require_admin(request, db)
    entries = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(500).all()
    return JSONResponse([serialize_feedback(entry) for entry in entries])


@router.delete("/api/admin/feedback/{feedback_id}")
async def api_admin_delete_feedback(feedback_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    admin = require_admin(request, db)
    entry = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    db.delete(entry)
    db.commit()
    log_action(db, admin, "Feedback Deleted", "feedback", feedback_id, f"By {entry.player_name}")
    return JSONResponse({"ok": True})


@router.get("/api/admin/audit-logs")
async def api_admin_audit_logs(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    require_admin(request, db)
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return JSONResponse([
        {"action": log.action, "targetType": log.target_type, "targetId": log.target_id, "details": log.details, "createdAt": log.created_at.isoformat() if log.created_at else None}
        for log in logs
    ])

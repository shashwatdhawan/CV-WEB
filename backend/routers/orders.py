from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from backend.database import get_db
from backend.dependencies import get_or_create_current_user
from backend.models import Order
from backend.schemas import CheckoutRequest
from backend.services import cart as cart_service
from backend.services.bot_integration import build_purchase_ticket_payload
from backend.services.orders import create_order_from_cart, serialize_order


router = APIRouter()


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    if not request.app.state.current_user(request):
        return RedirectResponse("/login")
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "orders.html")


@router.get("/orders/{order_number}", response_class=HTMLResponse)
async def order_detail_page(request: Request, order_number: str):
    if not request.app.state.current_user(request):
        return RedirectResponse("/login")
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "order_detail.html")


@router.post("/api/checkout")
async def api_checkout(payload: CheckoutRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    user = get_or_create_current_user(request, db)
    cart = cart_service.get_or_create_cart(db, user)
    try:
        order = create_order_from_cart(db, user, cart, payload.coupon_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse({"message": "Order successfully created.", "order": serialize_order(order), "botPayload": build_purchase_ticket_payload(order)})


@router.get("/api/orders")
async def api_orders(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    user = get_or_create_current_user(request, db)
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return JSONResponse([serialize_order(order) for order in orders])


@router.get("/api/orders/{order_number}")
async def api_order_detail(order_number: str, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    user = get_or_create_current_user(request, db)
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    if order.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=404, detail="Order not found.")
    return JSONResponse(serialize_order(order))

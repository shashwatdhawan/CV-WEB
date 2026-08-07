import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import Order, User
from backend.schemas import BotOrderLookupRequest, StatusUpdateRequest
from backend.services.bot_integration import build_purchase_ticket_payload
from backend.services.orders import serialize_order, update_order_status


router = APIRouter()


def require_bot_secret(x_bot_api_secret: str | None = Header(default=None)) -> None:
    if not settings.bot_api_secret:
        raise HTTPException(status_code=500, detail="BOT_API_SECRET is not configured.")
    if not x_bot_api_secret or not secrets.compare_digest(x_bot_api_secret, settings.bot_api_secret):
        raise HTTPException(status_code=401, detail="Invalid bot API secret.")


def get_order_or_404(db: Session, order_number: str) -> Order:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


def serialize_customer(user: User | None) -> dict:
    if user is None:
        return {}
    return {
        "id": user.id,
        "discordId": user.discord_id,
        "discordUsername": user.discord_username,
        "displayName": user.display_name,
        "avatar": user.avatar_url,
        "minecraftIgn": user.minecraft_ign,
        "minecraftUuid": user.minecraft_uuid,
        "minecraftAccountType": user.minecraft_account_type,
        "minecraftPremium": bool(user.minecraft_premium),
        "isAdmin": bool(user.is_admin),
        "joinedAt": user.website_joined_at.isoformat() if user.website_joined_at else None,
        "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
    }


@router.get("/internal/bot/validate")
async def internal_validate_bot_secret(_: None = Depends(require_bot_secret)) -> JSONResponse:
    return JSONResponse({"ok": True, "message": "Bot API secret is valid."})


@router.post("/internal/orders/new")
async def internal_new_order_payload(
    payload: BotOrderLookupRequest,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    order = get_order_or_404(db, payload.order_id)
    return JSONResponse(build_purchase_ticket_payload(order))


@router.get("/internal/orders/{order_number}")
async def internal_get_order(
    order_number: str,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return JSONResponse(serialize_order(get_order_or_404(db, order_number)))


@router.get("/internal/orders/{order_number}/ticket-payload")
async def internal_ticket_payload(
    order_number: str,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return JSONResponse(build_purchase_ticket_payload(get_order_or_404(db, order_number)))


@router.put("/internal/orders/{order_number}/status")
async def internal_update_order_status(
    order_number: str,
    payload: StatusUpdateRequest,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    order = get_order_or_404(db, order_number)
    try:
        updated = update_order_status(db, order, payload.status, None, payload.note or "Updated by Discord bot.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(serialize_order(updated))


@router.get("/internal/orders/{order_number}/customer")
async def internal_get_customer(
    order_number: str,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    order = get_order_or_404(db, order_number)
    return JSONResponse(serialize_customer(order.user))


@router.get("/internal/orders/{order_number}/items")
async def internal_get_items(
    order_number: str,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    order = get_order_or_404(db, order_number)
    return JSONResponse(serialize_order(order)["items"])


@router.get("/api/internal/bot/orders/{order_number}/ticket-payload")
async def legacy_internal_ticket_payload(
    order_number: str,
    _: None = Depends(require_bot_secret),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return JSONResponse(build_purchase_ticket_payload(get_order_or_404(db, order_number)))

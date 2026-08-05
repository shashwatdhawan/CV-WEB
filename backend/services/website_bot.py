from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Order
from backend.services.bot_integration import build_purchase_ticket_payload


async def create_discord_purchase_ticket(db: Session, order: Order) -> dict[str, Any]:
    if not settings.website_bot_url or not settings.website_ticket_secret:
        return {"ok": False, "ticket_channel_url": None, "requires_join": False, "join_url": settings.discord_invite_url, "message": "Bot URL or ticket secret is not configured."}

    payload = build_purchase_ticket_payload(order)
    bot_url = settings.website_bot_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{bot_url}/website/order-ticket",
                json=payload,
                headers={"X-Bot-Api-Secret": settings.website_ticket_secret},
            )
    except httpx.HTTPError:
        return {"ok": False, "ticket_channel_url": None, "requires_join": False, "join_url": settings.discord_invite_url, "message": "Discord bot API is unavailable."}

    if response.status_code >= 400:
        return {"ok": False, "ticket_channel_url": None, "requires_join": False, "join_url": settings.discord_invite_url, "message": "Discord bot API rejected the order request."}

    data = response.json()
    ticket_url = data.get("ticket_channel_url")
    if not ticket_url:
        return {
            "ok": False,
            "ticket_channel_url": None,
            "requires_join": bool(data.get("requires_join")),
            "join_url": data.get("join_url") or settings.discord_invite_url,
            "message": data.get("message") or "Ticket is not ready yet.",
        }

    order.ticket_channel_url = ticket_url
    db.commit()
    db.refresh(order)
    return {"ok": True, "ticket_channel_url": ticket_url, "requires_join": False, "join_url": settings.discord_invite_url, "message": "Discord ticket created."}

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from backend import crud
from backend.database import get_db
from backend.models import User
from backend.schemas import MinecraftLinkRequest
from backend.services.minecraft import MinecraftLookupError, fetch_minecraft_profile


router = APIRouter()


def iso_date(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def serialize_profile(user: User) -> dict[str, Any]:
    return {
        "discord": {
            "id": user.discord_id,
            "display_name": user.display_name,
            "username": user.discord_username,
            "avatar": user.avatar_url,
        },
        "minecraft": {
            "ign": user.minecraft_ign,
            "uuid": user.minecraft_uuid,
            "head_url": user.minecraft_head_url,
            "avatar_url": user.minecraft_avatar_url,
            "linked": bool(user.minecraft_uuid),
        },
        "stats": {
            "purchases": user.purchase_count,
            "orders": user.order_count,
            "money_spent_inr": user.money_spent_inr,
        },
        "dates": {
            "joined": iso_date(user.website_joined_at),
            "last_login": iso_date(user.last_login_at),
        },
    }


def current_session_user(request: Request) -> dict[str, Any]:
    current_user = request.app.state.current_user(request)
    if not current_user or not current_user.get("id"):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return current_user


def get_current_profile_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    session_user = current_session_user(request)
    discord_id = str(session_user["id"])
    user = crud.get_user_by_discord_id(db, discord_id)
    if user is None:
        user = crud.upsert_discord_user(
            db,
            {
                "id": discord_id,
                "global_name": session_user.get("username"),
                "username": session_user.get("discord_username") or session_user.get("username"),
            },
            session_user.get("avatar") or "",
        )
    return user


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    if not request.app.state.current_user(request):
        return RedirectResponse("/login")
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "profile.html")


@router.get("/api/profile")
async def api_profile(user: User = Depends(get_current_profile_user)) -> JSONResponse:
    return JSONResponse(serialize_profile(user))


@router.get("/api/profile/minecraft")
async def api_minecraft_profile(user: User = Depends(get_current_profile_user)) -> JSONResponse:
    return JSONResponse(serialize_profile(user)["minecraft"])


@router.get("/api/profile/stats")
async def api_profile_stats(user: User = Depends(get_current_profile_user)) -> JSONResponse:
    return JSONResponse(serialize_profile(user)["stats"])


@router.put("/api/profile/minecraft")
async def update_minecraft_profile(
    payload: MinecraftLinkRequest,
    user: User = Depends(get_current_profile_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        profile = await fetch_minecraft_profile(payload.ign)
    except MinecraftLookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated = crud.update_minecraft_account(
        db,
        user,
        profile["ign"],
        profile["uuid"],
        profile["head_url"],
        profile["avatar_url"],
    )
    return JSONResponse(serialize_profile(updated))

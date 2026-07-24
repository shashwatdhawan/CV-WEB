from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from backend import crud
from backend.models import User


def get_session_user(request: Request) -> dict[str, Any]:
    current_user = request.app.state.current_user(request)
    if not current_user or not current_user.get("id"):
        raise HTTPException(status_code=401, detail="Please log in with Discord first.")
    return current_user


def get_or_create_current_user(request: Request, db: Session) -> User:
    session_user = get_session_user(request)
    user = crud.get_user_by_discord_id(db, str(session_user["id"]))
    if user is None:
        user = crud.upsert_discord_user(
            db,
            {
                "id": session_user["id"],
                "global_name": session_user.get("username"),
                "username": session_user.get("discord_username") or session_user.get("username"),
            },
            session_user.get("avatar") or "",
        )
    return user


def require_admin(request: Request, db: Session) -> User:
    user = get_or_create_current_user(request, db)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user

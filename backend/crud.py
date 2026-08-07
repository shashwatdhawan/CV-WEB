from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.models import MinecraftAccount, User


def get_user_by_discord_id(db: Session, discord_id: str) -> User | None:
    return db.query(User).filter(User.discord_id == discord_id).first()


def upsert_discord_user(db: Session, discord_user: dict[str, Any], avatar_url: str) -> User:
    discord_id = str(discord_user.get("id"))
    display_name = discord_user.get("global_name") or discord_user.get("username") or "Discord User"
    discord_username = discord_user.get("username") or display_name
    user = get_user_by_discord_id(db, discord_id)
    now = datetime.now(timezone.utc)

    if user is None:
        user = User(
            discord_id=discord_id,
            display_name=display_name,
            discord_username=discord_username,
            avatar_url=avatar_url,
            website_joined_at=now,
            last_login_at=now,
        )
        db.add(user)
    else:
        user.display_name = display_name
        user.discord_username = discord_username
        user.avatar_url = avatar_url
        user.last_login_at = now

    db.commit()
    db.refresh(user)
    return user


def update_minecraft_account(
    db: Session,
    user: User,
    ign: str,
    uuid: str | None,
    account_type: str,
    premium: bool,
    head_url: str,
    avatar_url: str,
) -> User:
    user.minecraft_ign = ign
    user.minecraft_uuid = uuid
    user.minecraft_account_type = account_type
    user.minecraft_premium = premium
    user.minecraft_head_url = head_url
    user.minecraft_avatar_url = avatar_url

    account = db.query(MinecraftAccount).filter(MinecraftAccount.user_id == user.id).first()
    if account is None:
        account = MinecraftAccount(user_id=user.id, ign=ign, uuid=uuid, account_type=account_type, premium=premium, head_url=head_url, avatar_url=avatar_url)
        db.add(account)
    else:
        account.ign = ign
        account.uuid = uuid
        account.account_type = account_type
        account.premium = premium
        account.head_url = head_url
        account.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user

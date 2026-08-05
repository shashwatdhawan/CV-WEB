from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discord_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    discord_username: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=False)
    website_joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    minecraft_ign: Mapped[str] = mapped_column(String(16), nullable=True)
    minecraft_uuid: Mapped[str] = mapped_column(String(40), nullable=True)
    minecraft_head_url: Mapped[str] = mapped_column(String(500), nullable=True)
    minecraft_avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    money_spent_inr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

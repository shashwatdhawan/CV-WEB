import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import AdminInvitationCode, User
from backend.services.audit import log_action


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def redeem_admin_code(db: Session, user: User, code: str) -> str:
    cleaned = code.strip()
    if not cleaned:
        raise ValueError("Enter an admin code.")

    admin_count = db.query(User).filter(User.is_admin.is_(True)).count()
    if admin_count == 0 and settings.admin_setup_code and cleaned == settings.admin_setup_code:
        user.is_admin = True
        db.commit()
        log_action(db, user, "Admin Bootstrapped", "user", user.id, "First admin created with setup code.")
        return "First admin access enabled."

    invite = db.query(AdminInvitationCode).filter(AdminInvitationCode.code_hash == hash_code(cleaned)).first()
    if invite is None or invite.used:
        raise ValueError("Invalid admin code.")
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise ValueError("Admin code expired.")

    invite.used = True
    invite.redeemed_by_user_id = user.id
    invite.redeemed_at = datetime.now(timezone.utc)
    user.is_admin = True
    db.commit()
    log_action(db, user, "Admin Promoted", "user", user.id, "Redeemed admin invitation code.")
    return "Admin access enabled."

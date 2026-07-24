from sqlalchemy.orm import Session

from backend.models import AuditLog, User


def log_action(db: Session, actor: User | None, action: str, target_type: str = "", target_id: str = "", details: str = "") -> None:
    db.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            target_type=target_type,
            target_id=str(target_id or ""),
            details=details,
        )
    )
    db.commit()

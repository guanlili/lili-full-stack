import logging
import uuid
from typing import Any

from sqlmodel import Session

from app.models import AuditLog, User

logger = logging.getLogger(__name__)


def record_audit(
    *,
    session: Session,
    actor: User | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Persist an audit event without allowing logging failures to break business actions."""
    try:
        session.add(
            AuditLog(
                actor_user_id=actor.id if actor else None,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                details=details,
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to persist audit event: %s", action)

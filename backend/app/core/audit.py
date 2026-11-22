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
    """Persist an audit event in its own transaction.

    用调用方 Session 的同一 bind（引擎，测试时即被覆盖的测试引擎）新开独立
    连接提交：审计失败不回滚业务写入，业务回滚也不会带走已提交的审计。
    已知取舍：审计落库瞬间持有第二条池连接（毫秒级），默认池 5+10 时约 7+
    并发审计请求才开始排队；高并发项目调大 DB_POOL_SIZE/DB_MAX_OVERFLOW。
    """
    try:
        with Session(session.get_bind()) as audit_session:
            audit_session.add(
                AuditLog(
                    actor_user_id=actor.id if actor else None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    details=details,
                )
            )
            audit_session.commit()
    except Exception:
        logger.exception("Failed to persist audit event: %s", action)

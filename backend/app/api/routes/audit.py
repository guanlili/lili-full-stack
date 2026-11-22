import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import col, delete, func, select

from app.api.deps import SessionDep, get_current_active_superuser
from app.core.config import settings
from app.models import AuditLog, AuditLogPublic, AuditLogsPublic, User

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    # 内部审计是管理员能力：与角色权限页一致走超管门禁，不进可授予权限集
    dependencies=[Depends(get_current_active_superuser)],
)


def _prune_expired_audit_logs(session: SessionDep) -> None:
    """配置保留期后，超管查看审计时顺带清理过期行（读路径打扫，不占写路径）。"""
    retention = settings.AUDIT_LOG_RETENTION_DAYS
    if retention <= 0:
        return
    cutoff = datetime.now(UTC) - timedelta(days=retention)
    session.exec(delete(AuditLog).where(col(AuditLog.created_at) < cutoff))
    session.commit()


@router.get("/", response_model=AuditLogsPublic)
def read_audit_logs(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    action: Annotated[str | None, Query(max_length=100)] = None,
    actor_user_id: Annotated[uuid.UUID | None, Query()] = None,
    resource_type: Annotated[str | None, Query(max_length=100)] = None,
) -> Any:
    """超管分页查询内部审计日志（时间倒序，可按动作/操作者/资源类型过滤）。"""
    _prune_expired_audit_logs(session)
    conditions = []
    if action:
        conditions.append(col(AuditLog.action).icontains(action))
    if actor_user_id is not None:
        conditions.append(col(AuditLog.actor_user_id) == actor_user_id)
    if resource_type:
        conditions.append(col(AuditLog.resource_type).icontains(resource_type))

    count = session.exec(
        select(func.count()).select_from(AuditLog).where(*conditions)
    ).one()
    rows = session.exec(
        select(AuditLog, User.email)
        .outerjoin(User, col(User.id) == col(AuditLog.actor_user_id))
        .where(*conditions)
        .order_by(col(AuditLog.created_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    data = [
        AuditLogPublic(**log.model_dump(), actor_email=email) for log, email in rows
    ]
    return AuditLogsPublic(data=data, count=count)

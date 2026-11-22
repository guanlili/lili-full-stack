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
    """配置保留期后，超管查看审计时顺带清理过期行（读路径打扫，不占写路径）。

    分批删除：首次配置保留期时过期行可能很多，一次性大 DELETE 会造成长事务
    与 WAL 尖峰；每批独立提交，删不完留给下次查看继续。
    """
    retention = settings.AUDIT_LOG_RETENTION_DAYS
    if retention <= 0:
        return
    cutoff = datetime.now(UTC) - timedelta(days=retention)
    for _ in range(20):  # 单次查看最多清 20 批，避免请求超时
        deleted = session.exec(
            delete(AuditLog).where(
                col(AuditLog.id).in_(
                    select(AuditLog.id)
                    .where(col(AuditLog.created_at) < cutoff)
                    .limit(5_000)
                )
            )
        ).rowcount
        session.commit()
        if not deleted:
            break


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
        # autoescape：把用户输入里的 %/_ 当字面量而不是通配符
        conditions.append(col(AuditLog.action).icontains(action, autoescape=True))
    if actor_user_id is not None:
        conditions.append(col(AuditLog.actor_user_id) == actor_user_id)
    if resource_type:
        conditions.append(
            col(AuditLog.resource_type).icontains(resource_type, autoescape=True)
        )

    count = session.exec(
        select(func.count()).select_from(AuditLog).where(*conditions)
    ).one()
    rows = session.exec(
        select(AuditLog, User.email)
        .outerjoin(User, col(User.id) == col(AuditLog.actor_user_id))
        .where(*conditions)
        # id 作 tiebreaker：created_at 相同时分页才稳定（不重复不丢行）
        .order_by(col(AuditLog.created_at).desc(), col(AuditLog.id).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    data = [
        AuditLogPublic(**log.model_dump(), actor_email=email) for log, email in rows
    ]
    return AuditLogsPublic(data=data, count=count)

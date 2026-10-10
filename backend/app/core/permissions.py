"""Page registry shared by navigation, access checks and role configuration."""

from dataclasses import dataclass

from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.models import Permission, Role, RolePermission, User, UserRole

VISITOR_ROLE = "访客"


@dataclass(frozen=True)
class PagePermission:
    path: str
    codename: str
    title: str
    admin_only: bool = False


PAGES = (
    PagePermission("/", "dashboard.view", "工作台"),
    PagePermission("/settings", "profile.view", "账号设置"),
    PagePermission("/admin", "users.view", "用户管理"),
    PagePermission("/roles", "roles.manage", "角色权限", admin_only=True),
)
GRANTABLE_PERMISSIONS = {page.codename for page in PAGES if not page.admin_only}


def seed_permissions(session: Session) -> None:
    """Only seed missing entries; never overwrite administrator choices."""
    for page in PAGES:
        if (
            session.exec(
                select(Permission).where(Permission.codename == page.codename)
            ).first()
            is None
        ):
            session.add(Permission(codename=page.codename, description=page.title))
    session.flush()
    visitor = session.exec(select(Role).where(Role.name == VISITOR_ROLE)).first()
    if visitor is None:
        visitor = Role(
            name=VISITOR_ROLE, description="未分配其他角色的普通账号默认使用此角色"
        )
        session.add(visitor)
        session.flush()
        for permission in session.exec(
            select(Permission).where(
                col(Permission.codename).in_(["dashboard.view", "profile.view"])
            )
        ):
            session.add(RolePermission(role_id=visitor.id, permission_id=permission.id))
    session.commit()


def effective_permissions(session: Session, user: User) -> set[str]:
    if user.is_superuser:
        return {page.codename for page in PAGES}
    role_ids = list(
        session.exec(select(UserRole.role_id).where(UserRole.user_id == user.id))
    )
    if not role_ids:
        visitor = session.exec(select(Role).where(Role.name == VISITOR_ROLE)).first()
        role_ids = [visitor.id] if visitor else []
    if not role_ids:
        return set()
    statement = (
        select(Permission.codename)
        .join(RolePermission, col(RolePermission.permission_id) == col(Permission.id))
        .where(col(RolePermission.role_id).in_(role_ids))
    )
    return set(session.exec(statement)) & GRANTABLE_PERMISSIONS


def check_permission(session: Session, user: User, codename: str) -> None:
    if codename not in {page.codename for page in PAGES}:
        raise HTTPException(status_code=403, detail="Unknown permission")
    if codename not in effective_permissions(session, user):
        raise HTTPException(status_code=403, detail="Permission denied")

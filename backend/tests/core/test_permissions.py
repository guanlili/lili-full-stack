import uuid

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.permissions import (
    GRANTABLE_PERMISSIONS,
    PAGES,
    check_permission,
    effective_permissions,
)
from app.models import Permission, Role, RolePermission, User, UserRole
from tests.utils.user import create_random_user


def _permission(session: Session, codename: str) -> Permission:
    permission = session.exec(
        select(Permission).where(Permission.codename == codename)
    ).first()
    assert permission is not None
    return permission


def _grant_role(session: Session, user: User, codenames: list[str]) -> Role:
    role = Role(name=f"role-{uuid.uuid4().hex}")
    session.add(role)
    session.flush()
    for codename in codenames:
        session.add(
            RolePermission(
                role_id=role.id, permission_id=_permission(session, codename).id
            )
        )
    session.add(UserRole(user_id=user.id, role_id=role.id))
    session.commit()
    return role


def test_superuser_has_every_page_permission(db: Session) -> None:
    admin = create_random_user(db)
    admin.is_superuser = True
    db.add(admin)
    db.commit()

    assert effective_permissions(db, admin) == {page.codename for page in PAGES}


def test_roleless_user_falls_back_to_visitor(db: Session) -> None:
    user = create_random_user(db)
    perms = effective_permissions(db, user)
    # 访客角色默认持有工作台与账号设置两项可授予权限
    assert perms == {"dashboard.view", "profile.view"}


def test_custom_role_permissions_intersect_grantable(db: Session) -> None:
    user = create_random_user(db)
    # users.view 可授予；audit.view 为管理员专属，即使挂到角色上也会被交集剔除
    _grant_role(db, user, ["users.view", "audit.view"])

    perms = effective_permissions(db, user)
    assert "users.view" in perms
    assert "audit.view" not in perms
    assert perms <= GRANTABLE_PERMISSIONS


def test_check_permission_allows_granted(db: Session) -> None:
    user = create_random_user(db)
    # 访客默认具备 dashboard.view，不应抛异常
    check_permission(db, user, "dashboard.view")


def test_check_permission_denied_without_permission(db: Session) -> None:
    user = create_random_user(db)
    with pytest.raises(HTTPException) as exc:
        check_permission(db, user, "roles.manage")
    assert exc.value.status_code == 403
    assert exc.value.detail == "Permission denied"


def test_check_permission_unknown_codename(db: Session) -> None:
    user = create_random_user(db)
    with pytest.raises(HTTPException) as exc:
        check_permission(db, user, "not.a.real.permission")
    assert exc.value.status_code == 403
    assert exc.value.detail == "Unknown permission"

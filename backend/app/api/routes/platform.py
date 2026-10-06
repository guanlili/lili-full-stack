import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.audit import record_audit
from app.models import (
    AuditLog,
    AuditLogPublic,
    AuditLogsPublic,
    Permission,
    PermissionPublic,
    Role,
    RoleCreate,
    RolePermission,
    RolePublic,
    RolesPublic,
    User,
    UserRole,
    UserRolesPublic,
    UserRolesUpdate,
)

router = APIRouter(tags=["platform"])


@router.get(
    "/roles",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolesPublic,
)
def read_roles(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    count = session.exec(select(func.count()).select_from(Role)).one()
    roles = session.exec(
        select(Role).order_by(col(Role.name)).offset(skip).limit(limit)
    ).all()
    return RolesPublic(
        data=[RolePublic.model_validate(role) for role in roles], count=count
    )


@router.post(
    "/roles",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
)
def create_role(
    *, session: SessionDep, role_in: RoleCreate, current_user: CurrentUser
) -> Role:
    if session.exec(select(Role).where(Role.name == role_in.name)).first():
        raise HTTPException(status_code=409, detail="Role already exists")
    role = Role.model_validate(role_in)
    session.add(role)
    session.commit()
    session.refresh(role)
    record_audit(
        session=session,
        actor=current_user,
        action="role.created",
        resource_type="role",
        resource_id=role.id,
        details={"name": role.name},
    )
    return role


@router.get(
    "/roles/{role_id}/permissions",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[PermissionPublic],
)
def read_role_permissions(role_id: uuid.UUID, session: SessionDep) -> list[Permission]:
    if session.get(Role, role_id) is None:
        raise HTTPException(status_code=404, detail="Role not found")
    statement = (
        select(Permission)
        .join(RolePermission, col(RolePermission.permission_id) == col(Permission.id))
        .where(col(RolePermission.role_id) == role_id)
        .order_by(col(Permission.codename))
    )
    return list(session.exec(statement).all())


@router.put(
    "/users/{user_id}/roles",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserRolesPublic,
)
def update_user_roles(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    body: UserRolesUpdate,
    current_user: CurrentUser,
) -> UserRolesPublic:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    roles = list(
        session.exec(select(Role).where(col(Role.id).in_(body.role_ids))).all()
    )
    if len(roles) != len(set(body.role_ids)):
        raise HTTPException(status_code=400, detail="One or more roles do not exist")
    for existing in session.exec(
        select(UserRole).where(UserRole.user_id == user_id)
    ).all():
        session.delete(existing)
    for role in roles:
        session.add(UserRole(user_id=user_id, role_id=role.id))
    session.commit()
    record_audit(
        session=session,
        actor=current_user,
        action="user.roles_updated",
        resource_type="user",
        resource_id=user_id,
        details={"role_ids": [str(role.id) for role in roles]},
    )
    return UserRolesPublic(data=[RolePublic.model_validate(role) for role in roles])


@router.get(
    "/users/{user_id}/roles",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserRolesPublic,
)
def read_user_roles(user_id: uuid.UUID, session: SessionDep) -> UserRolesPublic:
    if session.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    statement = (
        select(Role)
        .join(UserRole, col(UserRole.role_id) == col(Role.id))
        .where(col(UserRole.user_id) == user_id)
        .order_by(col(Role.name))
    )
    return UserRolesPublic(
        data=[RolePublic.model_validate(role) for role in session.exec(statement)]
    )


@router.get(
    "/audit-logs",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=AuditLogsPublic,
)
def read_audit_logs(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> AuditLogsPublic:
    count = session.exec(select(func.count()).select_from(AuditLog)).one()
    logs = session.exec(
        select(AuditLog)
        .order_by(col(AuditLog.created_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return AuditLogsPublic(
        data=[AuditLogPublic.model_validate(log) for log in logs], count=count
    )

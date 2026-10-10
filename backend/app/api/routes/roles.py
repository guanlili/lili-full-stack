import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, delete, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.audit import record_audit
from app.core.permissions import GRANTABLE_PERMISSIONS
from app.models import (
    Permission,
    Role,
    RoleCreate,
    RoleDetailPublic,
    RolePermission,
    RolePermissionsUpdate,
    RolePublic,
    User,
    UserRole,
    UserRolesPublic,
    UserRolesUpdate,
)

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(get_current_active_superuser)],
)


def get_role(session: SessionDep, role_id: uuid.UUID) -> Role:
    role = session.exec(
        select(Role).where(Role.id == role_id).with_for_update()
    ).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


def role_detail(session: SessionDep, role: Role) -> RoleDetailPublic:
    permissions = session.exec(
        select(Permission.codename)
        .join(RolePermission, col(RolePermission.permission_id) == col(Permission.id))
        .where(RolePermission.role_id == role.id)
    ).all()
    return RoleDetailPublic(
        **role.model_dump(),
        permissions=sorted(set(permissions) & GRANTABLE_PERMISSIONS),
    )


@router.get("/", response_model=list[RoleDetailPublic])
def read_roles(session: SessionDep) -> list[RoleDetailPublic]:
    return [
        role_detail(session, role)
        for role in session.exec(select(Role).order_by(Role.name))
    ]


@router.post("/", response_model=RoleDetailPublic)
def create_role(
    session: SessionDep, current_user: CurrentUser, body: RoleCreate
) -> RoleDetailPublic:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Role name cannot be blank")
    role = Role(name=name, description=body.description)
    session.add(role)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Role name already exists") from exc
    session.refresh(role)
    record_audit(
        session=session,
        actor=current_user,
        action="role.created",
        resource_type="role",
        resource_id=role.id,
    )
    return role_detail(session, role)


@router.put("/{role_id}/permissions", response_model=RoleDetailPublic)
def update_permissions(
    session: SessionDep,
    current_user: CurrentUser,
    role_id: uuid.UUID,
    body: RolePermissionsUpdate,
) -> RoleDetailPublic:
    role = get_role(session, role_id)
    if not set(body.permissions).issubset(GRANTABLE_PERMISSIONS):
        raise HTTPException(
            status_code=422, detail="Unknown or administrator-only permission"
        )
    permissions = session.exec(
        select(Permission).where(col(Permission.codename).in_(body.permissions))
    ).all()
    if len(permissions) != len(set(body.permissions)):
        raise HTTPException(
            status_code=422, detail="Permission catalog is not initialized"
        )
    session.exec(delete(RolePermission).where(col(RolePermission.role_id) == role.id))
    for permission in permissions:
        session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    session.commit()
    record_audit(
        session=session,
        actor=current_user,
        action="role.permissions_updated",
        resource_type="role",
        resource_id=role.id,
        details={"permissions": sorted(set(body.permissions))},
    )
    return role_detail(session, role)


@router.get("/users/{user_id}", response_model=UserRolesPublic)
def read_user_roles(session: SessionDep, user_id: uuid.UUID) -> UserRolesPublic:
    if session.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    roles = session.exec(
        select(Role)
        .join(UserRole, col(UserRole.role_id) == col(Role.id))
        .where(UserRole.user_id == user_id)
    ).all()
    return UserRolesPublic(data=[RolePublic.model_validate(role) for role in roles])


@router.put("/users/{user_id}", response_model=UserRolesPublic)
def update_user_roles(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    body: UserRolesUpdate,
) -> UserRolesPublic:
    target = session.exec(
        select(User).where(User.id == user_id).with_for_update()
    ).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_superuser:
        raise HTTPException(
            status_code=403, detail="Administrators have immutable full access"
        )
    roles = session.exec(select(Role).where(col(Role.id).in_(body.role_ids))).all()
    if len(roles) != len(set(body.role_ids)):
        raise HTTPException(status_code=422, detail="Unknown role")
    session.exec(delete(UserRole).where(col(UserRole.user_id) == user_id))
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
    return read_user_roles(session, user_id)

import logging

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine, init_db
from app.models import Permission, Role, RolePermission, User, UserRole

DEFAULT_PERMISSIONS = {
    "users.read": "查看用户",
    "users.write": "管理用户",
    "audit.read": "查看审计日志",
    "settings.write": "修改系统配置",
    "files.write": "上传和管理文件",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        permissions: dict[str, Permission] = {}
        for codename, description in DEFAULT_PERMISSIONS.items():
            permission = session.exec(
                select(Permission).where(Permission.codename == codename)
            ).first()
            if permission is None:
                permission = Permission(codename=codename, description=description)
                session.add(permission)
                session.flush()
            permissions[codename] = permission

        admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
        if admin_role is None:
            admin_role = Role(name="admin", description="系统管理员")
            session.add(admin_role)
            session.flush()
        for permission in permissions.values():
            if (
                session.exec(
                    select(RolePermission).where(
                        RolePermission.role_id == admin_role.id,
                        RolePermission.permission_id == permission.id,
                    )
                ).first()
                is None
            ):
                session.add(
                    RolePermission(role_id=admin_role.id, permission_id=permission.id)
                )

        superuser = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        if (
            superuser
            and session.exec(
                select(UserRole).where(
                    UserRole.user_id == superuser.id, UserRole.role_id == admin_role.id
                )
            ).first()
            is None
        ):
            session.add(UserRole(user_id=superuser.id, role_id=admin_role.id))
        session.commit()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()

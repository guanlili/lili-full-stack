import logging

from sqlmodel import Session

from app.core.db import engine, init_db

# 权限与角色播种统一在 core/permissions.seed_permissions（PAGES 注册表 + 访客角色），
# 超管账号由 init_db 创建。曾在此播种的 users.read 等 codename 不在 PAGES 注册表中，
# check_permission 无法识别（"安慰剂"权限），已移除。
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()

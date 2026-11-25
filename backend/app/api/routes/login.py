"""兼容垫片：历史 `from app.api.routes import login` 仍可用。

实现已按职责拆分到 auth 子包（session / password），本文件保留 login.router
聚合引用，避免改动 api/main.py 之外的历史导入。
"""

from app.api.routes.auth import router

__all__ = ["router"]

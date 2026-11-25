"""认证路由子包。

- session.py：登录 / 刷新 / 登出 / 演示凭据 / token 自检
- password.py：密码找回 / 重置 / 重置邮件 HTML 预览
两个子路由器共用 tags=["login"]，由本包聚合后挂到 api_router。
"""

from fastapi import APIRouter

from app.api.routes.auth import password, session

router = APIRouter()
router.include_router(session.router)
router.include_router(password.router)

"""refresh token Cookie 共享常量与辅助函数。

会话路由（session.py）与登出/刷新共用同一份 Cookie 读写逻辑，抽到此处避免重复。
"""

from fastapi import Response

from app.core.config import settings

# refresh token 走 HttpOnly Cookie（前端 JS 不可读，XSS 无法窃取长命凭据）；
# Path 限定到登录端点族（/login/*），业务接口不会携带。SameSite=Lax 阻止绝大多数
# 跨站 POST 携带（注意：Chrome 对新种 cookie 有约 2 分钟的 Lax+POST 例外窗口，
# 此窗口内跨站顶级 POST 可触达 refresh/logout，影响限于强制轮换/登出 DoS；
# 对 CSRF 有强合规要求的客户项目再加 Origin 校验）。不能只限 /login/refresh——
# logout 也需要读到 cookie 才能吊销服务端 token。
REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = f"{settings.API_V1_STR}/login"


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        # local 开发走 http（vite:5173 → backend:8000），Secure 只在生产/预发开启
        secure=settings.ENVIRONMENT != "local",
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)

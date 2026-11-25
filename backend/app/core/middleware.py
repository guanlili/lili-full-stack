"""HTTP 安全中间件：响应安全头 + 写操作 Origin 白名单校验。

两层纵深：
- 安全头：后端自身补基础响应头，不依赖前置 nginx（后端被直连时仍有兜底）。
  HSTS 不在此加：TLS 终止在宿主反向代理，HTTP 明文响应加 HSTS 会被浏览器忽略。
- Origin 校验：对不安全方法做来源白名单校验，补 SameSite=Lax 之外的 CSRF 纵深。
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

# 不触发 Origin 校验的安全方法（RFC 9110）
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

# 实际用到的请求头；CORS 不再用通配符，避免凭证场景下过度放行
ALLOWED_CORS_HEADERS = ("Authorization", "Content-Type")
ALLOWED_CORS_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def _origin_allowed(origin: str) -> bool:
    return origin.rstrip("/") in settings.all_cors_origins


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """给所有响应补基础安全头（已存在的头不覆盖）。"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        return response


class OriginCheckMiddleware(BaseHTTPMiddleware):
    """不安全方法的 Origin 白名单校验。

    浏览器跨站发起 POST/PUT/PATCH/DELETE 必带 ``Origin``；非浏览器客户端
    （curl、服务端调用、健康检查）通常不带 ``Origin``，予以放行。带 ``Origin``
    但不在白名单内的，直接 403，避免被跨站页面伪造携带 cookie 的请求。
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method not in SAFE_METHODS:
            origin = request.headers.get("Origin")
            if origin and not _origin_allowed(origin):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "跨站来源不被允许"},
                )
        return await call_next(request)

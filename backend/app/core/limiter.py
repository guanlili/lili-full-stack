from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """限流键：客户端真实 IP。

    生产链路是 nginx 反代（nginx.conf 把真实 IP 追加到 X-Forwarded-For 末尾），
    取最后一跳即可拿到真实来源且无法被请求方伪造轮换；无代理头时退回直连地址。
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


# 进程内内存计数：默认单 worker 部署下即全局限额；多 worker 时为每 worker 独立限额。
# 注意：slowapi 的 enabled 只认 bool（传 callable 恒为真值），运行期开关直接改属性。
limiter = Limiter(key_func=get_client_ip)
limiter.enabled = settings.RATE_LIMIT_ENABLED


async def rate_limit_exceeded_handler(
    # starlette 处理器接口要求两个参数，本处理器统一返回固定错误体
    request: Request,  # noqa: ARG001
    exc: Exception,  # noqa: ARG001
) -> JSONResponse:
    # 与 HTTPException 的 {"detail": ...} 错误体保持一致，前端可统一翻译
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests"},
    )

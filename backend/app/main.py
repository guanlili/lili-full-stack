import logging
import re
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine
from app.core.limiter import limiter, rate_limit_exceeded_handler
from app.core.logging import configure_logging

# 应用日志统一格式（幂等）；独立运行的脚本（prestart 等）各自调用同一入口
configure_logging()

# Fraction of requests traced by Sentry; full tracing quickly exhausts quotas.
SENTRY_TRACES_SAMPLE_RATE = 0.1
# 超过该耗时（毫秒）的请求记慢请求日志；普通请求只记一条访问日志
SLOW_REQUEST_MS = 1000
# Client-supplied IDs are echoed and logged, so only accept short, safe tokens.
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}")

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    yield
    # 优雅关停：归还连接池中的数据库连接
    engine.dispose()


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    # GlitchTip 与 Sentry 协议兼容；DSN 指向自建实例即可直连上报
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN), traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE
    )

# 交互式文档只在本地方便调试；预发/生产直接不挂载（含 openapi.json，不暴露 API 面）
docs_enabled = settings.ENVIRONMENT == "local"

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs_enabled else None,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    generate_unique_id_function=custom_generate_unique_id,
)
# 认证敏感接口限流（见 app/core/limiter.py 与 login 路由）
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未捕获异常统一兜底：记录堆栈 + 上报监控，返回与前端中文映射对齐的通用 500 体。

    不再向客户端透出原始英文报错或堆栈；HTTPException 由 FastAPI 自身处理器处理，
    不会走到这里。
    """
    logger.exception(
        "unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": request.headers.get("X-Request-ID", ""),
        },
    )
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器开了小差，请稍后重试"},
    )


@app.middleware("http")
async def request_id_middleware(request, call_next):
    incoming_id = request.headers.get("X-Request-ID", "")
    request_id = (
        incoming_id if REQUEST_ID_PATTERN.fullmatch(incoming_id) else str(uuid.uuid4())
    )
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    # Log the route template (e.g. /password-recovery/{email}) so path
    # parameters such as email addresses stay out of application logs.
    route = request.scope.get("route")
    path = route.path if isinstance(route, APIRoute) else request.url.path
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "latency_ms": elapsed_ms,
        },
    )
    if elapsed_ms >= SLOW_REQUEST_MS:
        logger.warning(
            "slow request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "latency_ms": elapsed_ms,
            },
        )
    return response


# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

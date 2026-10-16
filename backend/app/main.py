import logging
import re
import uuid

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

# Fraction of requests traced by Sentry; full tracing quickly exhausts quotas.
SENTRY_TRACES_SAMPLE_RATE = 0.1
# Client-supplied IDs are echoed and logged, so only accept short, safe tokens.
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}")


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN), traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE
    )

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    incoming_id = request.headers.get("X-Request-ID", "")
    request_id = (
        incoming_id if REQUEST_ID_PATTERN.fullmatch(incoming_id) else str(uuid.uuid4())
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    # Log the route template (e.g. /password-recovery/{email}) so path
    # parameters such as email addresses stay out of application logs.
    route = request.scope.get("route")
    logger.info(
        "request_id=%s method=%s path=%s status=%s",
        request_id,
        request.method,
        route.path if isinstance(route, APIRoute) else request.url.path,
        response.status_code,
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

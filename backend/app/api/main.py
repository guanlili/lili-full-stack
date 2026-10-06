from fastapi import APIRouter

from app.api.routes import (
    files,
    jobs,
    login,
    platform,
    private,
    users,
    utils,
)
from app.api.routes import (
    settings as settings_routes,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(platform.router)
api_router.include_router(files.router)
api_router.include_router(settings_routes.router)
api_router.include_router(jobs.router)
api_router.include_router(utils.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

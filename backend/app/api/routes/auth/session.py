import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import col, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.api.routes.auth._cookie import (
    REFRESH_COOKIE,
    clear_refresh_cookie,
    set_refresh_cookie,
)
from app.core import security
from app.core.audit import record_audit
from app.core.config import settings
from app.core.limiter import limiter
from app.core.sessions import (
    hash_refresh_token,
    issue_refresh_token,
    revoke_user_refresh_tokens,
)
from app.models import Message, RefreshToken, Token, User, UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(tags=["login"])


class DemoCredentials(BaseModel):
    username: EmailStr
    password: str


@router.post("/login/access-token")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login_access_token(
    request: Request,  # noqa: ARG001  # slowapi 限流装饰器要求注入
    response: Response,
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        record_audit(
            session=session,
            actor=None,
            action="login.failed",
            resource_type="session",
            details={"email": form_data.username[:255]},
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        record_audit(
            session=session,
            actor=user,
            action="login.failed",
            resource_type="session",
            details={"email": form_data.username[:255], "reason": "inactive_user"},
        )
        raise HTTPException(status_code=400, detail="Inactive user")
    record_audit(
        session=session,
        actor=user,
        action="login.success",
        resource_type="session",
        resource_id=user.id,
        details={"email": form_data.username[:255]},
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = issue_refresh_token(session=session, user_id=user.id)
    session.commit()
    # 长命 refresh token 只经 HttpOnly Cookie 下发（见 _cookie.py 注释），
    # 响应体不再携带；短命 access token 走 Authorization header
    set_refresh_cookie(response, refresh_token)
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=access_token_expires,
            token_version=user.token_version,
        ),
    )


@router.post("/login/refresh", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
def refresh_access_token(
    request: Request,  # noqa: ARG001  # slowapi 限流装饰器要求注入
    *,
    response: Response,
    session: SessionDep,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> Token:
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    token = session.exec(
        select(RefreshToken).where(
            col(RefreshToken.token_hash) == hash_refresh_token(refresh_cookie)
        )
    ).first()
    now = datetime.now(UTC)
    if token is None or token.revoked_at is not None or token.expires_at <= now:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    # Lock the user before the token, matching password changes/logout-all.
    # Re-read the token after waiting so a concurrent rotation cannot reuse it.
    user = session.exec(
        select(User).where(User.id == token.user_id).with_for_update()
    ).first()
    token = session.exec(
        select(RefreshToken)
        .where(RefreshToken.id == token.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if (
        token is None
        or token.revoked_at is not None
        or token.expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    token.revoked_at = now
    new_refresh_token = issue_refresh_token(session=session, user_id=user.id)
    session.commit()
    set_refresh_cookie(response, new_refresh_token)
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            token_version=user.token_version,
        ),
    )


@router.post("/login/logout", response_model=Message)
def logout(
    *,
    response: Response,
    session: SessionDep,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> Message:
    """Clear the refresh cookie and revoke its server-side token."""
    clear_refresh_cookie(response)
    if refresh_cookie:
        token = session.exec(
            select(RefreshToken).where(
                col(RefreshToken.token_hash) == hash_refresh_token(refresh_cookie)
            )
        ).first()
        if token is not None and token.revoked_at is None:
            token.revoked_at = datetime.now(UTC)
            session.add(token)
            session.commit()
            record_audit(
                session=session,
                actor=session.get(User, token.user_id),
                action="session.logout",
                resource_type="session",
                resource_id=token.user_id,
            )
    return Message(message="Logged out")


@router.post("/login/logout-all", response_model=Message)
def logout_all(
    *, response: Response, session: SessionDep, current_user: CurrentUser
) -> Message:
    """Revoke all existing access tokens for the current user."""
    current_user.token_version += 1
    revoke_user_refresh_tokens(session=session, user_id=current_user.id)
    session.add(current_user)
    session.commit()
    clear_refresh_cookie(response)
    record_audit(
        session=session,
        actor=current_user,
        action="session.revoked_all",
        resource_type="session",
        resource_id=current_user.id,
    )
    return Message(message="All sessions have been revoked")


@router.get("/login/demo-credentials", response_model=DemoCredentials)
def demo_credentials() -> DemoCredentials:
    """Return local-only demo credentials for the development login page."""
    if settings.ENVIRONMENT != "local":
        raise HTTPException(status_code=404, detail="Not found")
    return DemoCredentials(
        username=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user

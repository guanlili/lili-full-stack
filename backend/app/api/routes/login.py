import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import col, select

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.audit import record_audit
from app.core.config import settings
from app.core.limiter import limiter
from app.core.sessions import (
    hash_refresh_token,
    issue_refresh_token,
    revoke_user_refresh_tokens,
)
from app.models import (
    Message,
    NewPassword,
    RefreshToken,
    Token,
    User,
    UserPublic,
    UserUpdate,
)
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])

logger = logging.getLogger(__name__)

# refresh token 走 HttpOnly Cookie（前端 JS 不可读，XSS 无法窃取长命凭据）；
# Path 限定到刷新端点，其他请求不会携带。SameSite=Lax 阻止跨站 POST 携带，
# 天然防 CSRF，无需额外 CSRF token。
REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = f"{settings.API_V1_STR}/login/refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
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


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)


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
            details={"email": form_data.username},
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        record_audit(
            session=session,
            actor=user,
            action="login.failed",
            resource_type="session",
            details={"email": form_data.username, "reason": "inactive_user"},
        )
        raise HTTPException(status_code=400, detail="Inactive user")
    record_audit(
        session=session,
        actor=user,
        action="login.success",
        resource_type="session",
        resource_id=user.id,
        details={"email": form_data.username},
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = issue_refresh_token(session=session, user_id=user.id)
    session.commit()
    # 长命 refresh token 只经 HttpOnly Cookie 下发（见 REFRESH_COOKIE 注释），
    # 响应体不再携带；短命 access token 走 Authorization header
    _set_refresh_cookie(response, refresh_token)
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=access_token_expires,
            token_version=user.token_version,
        ),
    )


@router.post("/login/refresh", response_model=Token)
def refresh_access_token(
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
    _set_refresh_cookie(response, new_refresh_token)
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            token_version=user.token_version,
        ),
    )


@router.post("/login/logout", response_model=Message)
def logout(response: Response) -> Message:
    """Clear the refresh cookie (server-side token expires on its own rotation)."""
    _clear_refresh_cookie(response)
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
    _clear_refresh_cookie(response)
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


@router.post("/password-recovery/{email}")
@limiter.limit(settings.RATE_LIMIT_RECOVERY)
def recover_password(
    request: Request,  # noqa: ARG001  # slowapi 限流装饰器要求注入
    email: str,
    session: SessionDep,
) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    # Always return the same response to prevent email enumeration attacks
    # Only send email if user actually exists
    if user:
        if not settings.emails_enabled:
            # 邮件未配置（SMTP_HOST / EMAILS_FROM_EMAIL 缺失）时不能让接口 500，
            # 仍返回同样的防枚举响应，服务端记日志提醒运维
            logger.warning(
                "Password recovery requested for an existing user, but email is "
                "not configured (SMTP_HOST / EMAILS_FROM_EMAIL missing); "
                "no email sent."
            )
        else:
            password_reset_token = generate_password_reset_token(
                email=email, token_version=user.token_version
            )
            email_data = generate_reset_password_email(
                email_to=user.email, email=email, token=password_reset_token
            )
            send_email(
                email_to=user.email,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password/")
@limiter.limit(settings.RATE_LIMIT_RECOVERY)
def reset_password(
    request: Request,  # noqa: ARG001  # slowapi 限流装饰器要求注入
    session: SessionDep,
    body: NewPassword,
) -> Message:
    """
    Reset password
    """
    claims = verify_password_reset_token(token=body.token)
    if not claims:
        raise HTTPException(status_code=400, detail="Invalid token")
    # Lock the row so two concurrent submissions of one link cannot both succeed.
    user = session.exec(
        select(User).where(User.email == claims.email).with_for_update()
    ).first()
    if not user or user.token_version != claims.token_version:
        # Same error for unknown users and used/stale links to avoid enumeration
        raise HTTPException(status_code=400, detail="Invalid token")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user_in_update = UserUpdate(password=body.new_password)
    crud.update_user(
        session=session,
        db_user=user,
        user_in=user_in_update,
    )
    record_audit(
        session=session,
        actor=user,
        action="user.password_reset",
        resource_type="user",
        resource_id=user.id,
    )
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(
        email=email, token_version=user.token_version
    )
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(content=email_data.html_content)

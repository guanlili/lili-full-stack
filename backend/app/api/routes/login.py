import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import col, select

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.sessions import (
    hash_refresh_token,
    issue_refresh_token,
    revoke_user_refresh_tokens,
)
from app.models import (
    Message,
    NewPassword,
    RefreshToken,
    RefreshTokenRequest,
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


class DemoCredentials(BaseModel):
    username: EmailStr
    password: str


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = issue_refresh_token(session=session, user_id=user.id)
    session.commit()
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=access_token_expires,
            token_version=user.token_version,
        ),
        refresh_token=refresh_token,
    )


@router.post("/login/refresh", response_model=Token)
def refresh_access_token(*, session: SessionDep, body: RefreshTokenRequest) -> Token:
    token = session.exec(
        select(RefreshToken).where(
            col(RefreshToken.token_hash) == hash_refresh_token(body.refresh_token)
        )
    ).first()
    now = datetime.now(UTC)
    if token is None or token.revoked_at is not None or token.expires_at <= now:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = session.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    token.revoked_at = now
    new_refresh_token = issue_refresh_token(session=session, user_id=user.id)
    session.commit()
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            token_version=user.token_version,
        ),
        refresh_token=new_refresh_token,
    )


@router.post("/login/logout-all", response_model=Message)
def logout_all(*, session: SessionDep, current_user: CurrentUser) -> Message:
    """Revoke all existing access tokens for the current user."""
    current_user.token_version += 1
    revoke_user_refresh_tokens(session=session, user_id=current_user.id)
    session.add(current_user)
    session.commit()
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
def recover_password(email: str, session: SessionDep) -> Message:
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
            password_reset_token = generate_password_reset_token(email=email)
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
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        # Don't reveal that the user doesn't exist - use same error as invalid token
        raise HTTPException(status_code=400, detail="Invalid token")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user_in_update = UserUpdate(password=body.new_password)
    crud.update_user(
        session=session,
        db_user=user,
        user_in=user_in_update,
    )
    revoke_user_refresh_tokens(session=session, user_id=user.id)
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
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )

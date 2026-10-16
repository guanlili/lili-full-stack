import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, col, delete, select

from app.core.config import settings
from app.models import RefreshToken


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_refresh_token(*, session: Session, user_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    # Expired rows can never be used again; prune them so the table stays bounded.
    session.exec(
        delete(RefreshToken).where(
            col(RefreshToken.user_id) == user_id,
            col(RefreshToken.expires_at) <= now,
        )
    )
    raw_token = secrets.token_urlsafe(48)
    session.add(
        RefreshToken(
            token_hash=hash_refresh_token(raw_token),
            user_id=user_id,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return raw_token


def revoke_user_refresh_tokens(*, session: Session, user_id: uuid.UUID) -> None:
    now = datetime.now(UTC)
    tokens = session.exec(
        select(RefreshToken).where(
            col(RefreshToken.user_id) == user_id,
            col(RefreshToken.revoked_at).is_(None),
        )
    ).all()
    for token in tokens:
        token.revoked_at = now
        session.add(token)


def delete_user_refresh_tokens(*, session: Session, user_id: uuid.UUID) -> None:
    session.exec(delete(RefreshToken).where(col(RefreshToken.user_id) == user_id))

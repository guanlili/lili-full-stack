from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.api.deps import get_current_user, get_db
from app.core import security
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import create_user
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string


def test_get_db_yields_session() -> None:
    gen = get_db()
    try:
        session = next(gen)
        assert isinstance(session, Session)
    finally:
        gen.close()


def _access_token(
    user_id: object, token_version: int, typ: str = security.ACCESS_TOKEN_TYPE
) -> str:
    token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=15),
        token_version=token_version,
    )
    if typ != security.ACCESS_TOKEN_TYPE:
        # 替换 typ 后重新签名，模拟类型不符的合法签名 token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        payload["typ"] = typ
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=security.ALGORITHM)
    return token


def test_current_user_rejects_wrong_token_type(db: Session) -> None:
    user = create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    token = _access_token(
        user.id, user.token_version, typ=security.PASSWORD_RESET_TOKEN_TYPE
    )
    with pytest.raises(HTTPException) as exc:
        get_current_user(db, token)
    assert exc.value.status_code == 401


def test_current_user_rejects_unknown_user(db: Session) -> None:
    token = _access_token(uuid4(), token_version=0)
    with pytest.raises(HTTPException) as exc:
        get_current_user(db, token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found"


def test_current_user_rejects_inactive_user(db: Session) -> None:
    user = create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    user.is_active = False
    db.commit()
    token = _access_token(user.id, user.token_version)
    with pytest.raises(HTTPException) as exc:
        get_current_user(db, token)
    assert exc.value.status_code == 403

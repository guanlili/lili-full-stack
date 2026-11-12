from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.passwords import COMMON_PASSWORDS, validate_password_not_common
from app.core.security import verify_password
from app.crud import create_user
from app.models import User, UserCreate
from app.utils import generate_password_reset_token
from tests.utils.utils import random_email, random_lower_string


def _create_user(db: Session, *, password: str) -> User:
    return create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(),
            full_name="Policy Target",
            password=password,
            is_active=True,
            is_superuser=False,
        ),
    )


def test_create_user_rejects_common_password(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": "password123",
            "full_name": "Weak Password",
        },
    )
    assert r.status_code == 422
    assert "too common" in r.json()["detail"][0]["msg"]


def test_signup_rejects_common_password(client: TestClient) -> None:
    # .env.example 默认开放注册（本地开发语义），非开放环境下跳过
    if not settings.USERS_OPEN_REGISTRATION:
        return
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json={
            "email": random_email(),
            "password": "12345678",
            "full_name": "Weak Password",
        },
    )
    assert r.status_code == 422


def test_reset_password_rejects_common_password(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    user = _create_user(db, password=password)
    token = generate_password_reset_token(email=email, token_version=user.token_version)
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        json={"new_password": "qwerty123", "token": token},
    )
    assert r.status_code == 422
    # 被拒绝后原密码未被改动
    db.refresh(user)
    assert not verify_password("qwerty123", user.hashed_password)[0]


def test_change_password_rejects_common_password(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # 用超管验证（普通用户无 profile.view 权限会先 403）；
    # 422 发生在 schema 校验层，密码不会被真正修改，无状态残留
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json={
            "current_password": settings.FIRST_SUPERUSER_PASSWORD,
            "new_password": "welcome123",
        },
    )
    assert r.status_code == 422


def test_blacklist_entries_and_case_insensitivity() -> None:
    assert "PASSWORD123" not in COMMON_PASSWORDS  # 列表只存小写
    try:
        validate_password_not_common("PASSWORD123")  # 大写同样拦截
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    # 全部条目都满足长度下限（更短的交给 min_length）
    assert all(len(pw) >= 8 for pw in COMMON_PASSWORDS)
    # None（可选字段）直通
    assert validate_password_not_common(None) is None

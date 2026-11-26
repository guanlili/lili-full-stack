import jwt

from app.core import security
from app.core.config import settings
from app.utils import generate_password_reset_token, verify_password_reset_token


def _encode(claims: dict) -> str:
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=security.ALGORITHM)


def test_verify_reset_token_roundtrip() -> None:
    token = generate_password_reset_token(email="demo@example.com", token_version=3)
    claims = verify_password_reset_token(token)
    assert claims is not None
    assert claims.email == "demo@example.com"
    assert claims.token_version == 3


def test_verify_reset_token_invalid_signature() -> None:
    assert verify_password_reset_token("not-a-jwt") is None


def test_verify_reset_token_wrong_token_type() -> None:
    # access token 被当作重置令牌解析：typ 不匹配，应拒绝
    token = _encode(
        {"sub": "demo@example.com", "ver": 1, "typ": security.ACCESS_TOKEN_TYPE}
    )
    assert verify_password_reset_token(token) is None


def test_verify_reset_token_non_integer_version() -> None:
    token = _encode(
        {
            "sub": "demo@example.com",
            "ver": "not-an-int",
            "typ": security.PASSWORD_RESET_TOKEN_TYPE,
        }
    )
    assert verify_password_reset_token(token) is None


def test_verify_reset_token_missing_email() -> None:
    token = _encode({"ver": 1, "typ": security.PASSWORD_RESET_TOKEN_TYPE})
    assert verify_password_reset_token(token) is None

from unittest.mock import patch

import jwt
import pytest

from app.core import security
from app.core.config import settings
from app.utils import (
    generate_password_reset_token,
    generate_test_email,
    send_email,
    verify_password_reset_token,
)


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


def test_send_email_disabled_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    with pytest.raises(ValueError, match="no provided configuration"):
        send_email(email_to="demo@example.com", subject="s", html_content="<p></p>")


def test_send_email_tls_with_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setattr(settings, "SMTP_TLS", True)
    monkeypatch.setattr(settings, "SMTP_SSL", False)
    monkeypatch.setattr(settings, "SMTP_USER", "smtp-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-pass")

    with patch("app.utils.emails.message.Message") as mock_message:
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>hi</p>")

    smtp = mock_message.return_value.send.call_args.kwargs["smtp"]
    assert smtp["host"] == "smtp.example.com"
    assert smtp["tls"] is True
    assert smtp["user"] == "smtp-user"
    assert smtp["password"] == "smtp-pass"
    assert "ssl" not in smtp


def test_send_email_ssl_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setattr(settings, "SMTP_TLS", False)
    monkeypatch.setattr(settings, "SMTP_SSL", True)
    monkeypatch.setattr(settings, "SMTP_USER", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)

    with patch("app.utils.emails.message.Message") as mock_message:
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>hi</p>")

    smtp = mock_message.return_value.send.call_args.kwargs["smtp"]
    assert smtp["ssl"] is True
    assert "tls" not in smtp
    assert "user" not in smtp


def test_generate_test_email_renders_template() -> None:
    data = generate_test_email(email_to="reader@example.com")
    assert settings.PROJECT_NAME in data.subject
    assert "reader@example.com" in data.html_content
    assert data.html_content

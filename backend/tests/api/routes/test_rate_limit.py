import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.limiter import limiter

# 限流限额与 config.py 默认值联动；修改配置时同步这里
LOGIN_LIMIT = 10
RECOVERY_LIMIT = 5


@pytest.fixture(autouse=True)
def enable_rate_limit():
    """conftest 全局关闭限流，本文件单独打开并隔离计数器。"""
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.enabled = False
    limiter.reset()


def _login(client: TestClient, headers: dict[str, str] | None = None) -> None:
    client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "nobody@example.com", "password": "wrong"},
        headers=headers,
    )


def test_login_rate_limited(client: TestClient) -> None:
    for _ in range(LOGIN_LIMIT):
        _login(client)
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "nobody@example.com", "password": "wrong"},
    )
    assert r.status_code == 429
    assert r.json() == {"detail": "Too many requests"}


def test_rate_limit_keyed_by_forwarded_ip(client: TestClient) -> None:
    """不同 X-Forwarded-For 各自计数（生产链路取反代追加的最后一跳为限流键）。"""
    for _ in range(LOGIN_LIMIT):
        _login(client, headers={"X-Forwarded-For": "203.0.113.1"})
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "nobody@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "203.0.113.1"},
    )
    assert r.status_code == 429

    # 另一个 IP 不受影响
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "nobody@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "203.0.113.2"},
    )
    assert r.status_code == 400


def test_password_recovery_rate_limited(client: TestClient) -> None:
    for _ in range(RECOVERY_LIMIT):
        r = client.post(f"{settings.API_V1_STR}/password-recovery/nobody@example.com")
        assert r.status_code == 200
    r = client.post(f"{settings.API_V1_STR}/password-recovery/nobody@example.com")
    assert r.status_code == 429


def test_rate_limit_disabled_by_flag(client: TestClient) -> None:
    limiter.enabled = False
    for _ in range(LOGIN_LIMIT + 1):
        _login(client)
    # 未触发 429（均到达业务层并因凭据错误返回 400）
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "nobody@example.com", "password": "wrong"},
    )
    assert r.status_code == 400

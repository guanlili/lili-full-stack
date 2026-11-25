from fastapi.testclient import TestClient

from app.core.config import settings

LOGIN_URL = f"{settings.API_V1_STR}/login/access-token"
READY_URL = f"{settings.API_V1_STR}/utils/ready-check/"
EVIL_ORIGIN = "https://evil.example.com"


def test_security_headers_present_on_response(client: TestClient) -> None:
    """后端自身补基础安全头，不依赖前置 nginx。"""
    r = client.get(READY_URL)
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_origin_check_allows_whitelisted_origin(client: TestClient) -> None:
    """白名单 Origin 的写请求放行到业务层（不被 Origin 中间件 403）。"""
    r = client.post(
        LOGIN_URL,
        headers={"Origin": settings.FRONTEND_HOST},
        data={"username": "x", "password": "y"},
    )
    assert r.json().get("detail") != "跨站来源不被允许"
    assert r.status_code != 403


def test_origin_check_blocks_foreign_origin(client: TestClient) -> None:
    """不在白名单的 Origin 发起写请求，直接 403。"""
    r = client.post(
        LOGIN_URL,
        headers={"Origin": EVIL_ORIGIN},
        data={"username": "x", "password": "y"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "跨站来源不被允许"


def test_origin_check_allows_missing_origin(client: TestClient) -> None:
    """非浏览器客户端（curl/服务端/健康检查）不带 Origin，予以放行。"""
    r = client.post(LOGIN_URL, data={"username": "x", "password": "y"})
    assert r.json().get("detail") != "跨站来源不被允许"
    assert r.status_code != 403


def test_cors_preflight_methods_not_wildcard(client: TestClient) -> None:
    """预检返回的方法/头已收敛，不再用通配符。"""
    r = client.options(
        LOGIN_URL,
        headers={
            "Origin": settings.FRONTEND_HOST,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    allow_methods = r.headers.get("Access-Control-Allow-Methods", "")
    allow_headers = r.headers.get("Access-Control-Allow-Headers", "")
    assert "*" not in allow_methods
    assert "*" not in allow_headers
    assert "POST" in allow_methods
    assert "Content-Type" in allow_headers or "content-type" in allow_headers.lower()

import os
import subprocess
import sys

from fastapi.testclient import TestClient

from app.core.config import settings


def test_minimal_template_api_surface(client: TestClient) -> None:
    paths = client.get(f"{settings.API_V1_STR}/openapi.json").json()["paths"]
    removed = ("/files", "/jobs", "/settings")
    for path in paths:
        suffix = path.removeprefix(settings.API_V1_STR)
        assert not any(suffix.startswith(prefix) for prefix in removed), path
        assert suffix not in ("/users/export.csv", "/users/import.csv")
    assert f"{settings.API_V1_STR}/users/me" in paths
    assert f"{settings.API_V1_STR}/login/access-token" in paths
    # 审计查询已恢复为超管专用端点
    assert f"{settings.API_V1_STR}/audit-logs/" in paths


def test_docs_disabled_outside_local() -> None:
    """非 local 环境不挂载 /docs /redoc /openapi.json（不暴露 API 面）。"""
    code = (
        "import app.main; app = app.main.app; "
        "assert app.docs_url is None and app.redoc_url is None and app.openapi_url is None"
    )
    # 真实环境变量优先于 .env 文件（pydantic-settings 语义）；
    # 非 changethis 的占位值避免触发生产密钥校验（本测试只关心文档门禁）
    env = {
        **os.environ,
        "ENVIRONMENT": "production",
        "SECRET_KEY": "docs-gate-check-not-default",
        "POSTGRES_PASSWORD": "docs-gate-check-not-default",
        "FIRST_SUPERUSER_PASSWORD": "docs-gate-check-not-default",
    }
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr

from fastapi.testclient import TestClient

from app.core.config import settings


def test_minimal_template_api_surface(client: TestClient) -> None:
    paths = client.get(f"{settings.API_V1_STR}/openapi.json").json()["paths"]
    removed = ("/roles", "/permissions", "/audit-logs", "/files", "/jobs", "/settings")
    for path in paths:
        suffix = path.removeprefix(settings.API_V1_STR)
        assert not any(suffix.startswith(prefix) for prefix in removed), path
        assert suffix not in ("/users/export.csv", "/users/import.csv")
    assert f"{settings.API_V1_STR}/users/me" in paths
    assert f"{settings.API_V1_STR}/login/access-token" in paths

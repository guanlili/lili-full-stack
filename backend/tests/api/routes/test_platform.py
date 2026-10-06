import uuid

from fastapi.testclient import TestClient

from app.core.config import settings


def test_roles_and_audit_logs(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    role_name = f"reviewer-{uuid.uuid4().hex[:8]}"
    role_response = client.post(
        f"{settings.API_V1_STR}/roles",
        headers=superuser_token_headers,
        json={"name": role_name, "description": "只读审核角色"},
    )
    assert role_response.status_code == 200
    role = role_response.json()
    assert role["name"] == role_name

    roles_response = client.get(
        f"{settings.API_V1_STR}/roles", headers=superuser_token_headers
    )
    assert roles_response.status_code == 200
    assert any(item["id"] == role["id"] for item in roles_response.json()["data"])

    audit_response = client.get(
        f"{settings.API_V1_STR}/audit-logs", headers=superuser_token_headers
    )
    assert audit_response.status_code == 200
    assert any(
        item["action"] == "role.created" for item in audit_response.json()["data"]
    )


def test_system_settings(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.put(
        f"{settings.API_V1_STR}/settings/site.title",
        headers=superuser_token_headers,
        json={"value": "模板后台", "description": "页面标题"},
    )
    assert response.status_code == 200
    assert response.json()["value"] == "模板后台"

    list_response = client.get(
        f"{settings.API_V1_STR}/settings/", headers=superuser_token_headers
    )
    assert list_response.status_code == 200
    assert any(item["key"] == "site.title" for item in list_response.json())

    secret_response = client.put(
        f"{settings.API_V1_STR}/settings/api_key",
        headers=superuser_token_headers,
        json={"value": "must-not-be-stored"},
    )
    assert secret_response.status_code == 400


def test_enqueue_users_export(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.api.routes.jobs.run_user_export_job", lambda _job_id: None)
    response = client.post(
        f"{settings.API_V1_STR}/jobs/users-export",
        headers=superuser_token_headers,
    )
    assert response.status_code == 202
    assert response.json()["task_type"] == "users.export"

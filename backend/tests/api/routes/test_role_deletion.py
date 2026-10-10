import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import AuditLog, RolePermission
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email

PREFIX = settings.API_V1_STR


def create_role(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        f"{PREFIX}/roles/", headers=headers, json={"name": f"delete-{uuid.uuid4().hex}"}
    )
    assert response.status_code == 200
    return response.json()


def test_delete_role_permissions_and_audit(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    admin = superuser_token_headers
    role = create_role(client, admin)
    role_id = role["id"]
    path = f"{PREFIX}/roles/{role_id}"
    assert (
        client.put(
            f"{path}/permissions",
            headers=admin,
            json={"permissions": ["dashboard.view"]},
        ).status_code
        == 200
    )
    assert client.delete(path).status_code == 401
    assert client.delete(path, headers=normal_user_token_headers).status_code == 403
    assert client.delete(path, headers=admin).status_code == 200
    assert client.delete(path, headers=admin).status_code == 404
    assert (
        db.exec(
            select(RolePermission).where(RolePermission.role_id == uuid.UUID(role_id))
        ).first()
        is None
    )
    assert (
        db.exec(
            select(AuditLog).where(
                AuditLog.action == "role.deleted", AuditLog.resource_id == role_id
            )
        ).first()
        is not None
    )
    assert all(
        item["id"] != role_id
        for item in client.get(f"{PREFIX}/roles/", headers=admin).json()
    )


def test_default_and_assigned_roles_protected(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    admin = superuser_token_headers
    visitor = next(
        role
        for role in client.get(f"{PREFIX}/roles/", headers=admin).json()
        if role["is_default"]
    )
    assert (
        client.delete(f"{PREFIX}/roles/{visitor['id']}", headers=admin).status_code
        == 403
    )
    role = create_role(client, admin)
    headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    user_id = client.get(f"{PREFIX}/users/me", headers=headers).json()["id"]
    assignment = f"{PREFIX}/roles/users/{user_id}"
    assert (
        client.put(
            assignment, headers=admin, json={"role_ids": [role["id"]]}
        ).status_code
        == 200
    )
    listed = next(
        item
        for item in client.get(f"{PREFIX}/roles/", headers=admin).json()
        if item["id"] == role["id"]
    )
    assert listed["user_count"] == 1
    assert (
        client.delete(f"{PREFIX}/roles/{role['id']}", headers=admin).status_code == 409
    )
    assert client.get(assignment, headers=admin).json()["data"][0]["id"] == role["id"]
    assert (
        client.put(assignment, headers=admin, json={"role_ids": []}).status_code == 200
    )
    assert (
        client.delete(f"{PREFIX}/roles/{role['id']}", headers=admin).status_code == 200
    )


def test_assignment_and_deletion_are_serialized(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    admin = superuser_token_headers
    role = create_role(client, admin)
    headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    user_id = client.get(f"{PREFIX}/users/me", headers=headers).json()["id"]
    barrier = Barrier(2)

    def assign() -> int:
        barrier.wait(timeout=5)
        return client.put(
            f"{PREFIX}/roles/users/{user_id}",
            headers=admin,
            json={"role_ids": [role["id"]]},
        ).status_code

    def remove() -> int:
        barrier.wait(timeout=5)
        return client.delete(f"{PREFIX}/roles/{role['id']}", headers=admin).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        assigned = executor.submit(assign)
        deleted = executor.submit(remove)
        outcome = (assigned.result(timeout=10), deleted.result(timeout=10))
    assert outcome in {(200, 409), (422, 200)}

import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.permissions import check_permission, seed_permissions
from app.models import User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email

PREFIX = settings.API_V1_STR


def test_visitor_defaults(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    headers = normal_user_token_headers
    access = client.get(f"{PREFIX}/access/me", headers=headers)
    assert access.status_code == 200
    assert set(access.json()["permissions"]) == {"dashboard.view", "profile.view"}
    assert client.get(f"{PREFIX}/roles/", headers=headers).status_code == 403
    assert client.get(f"{PREFIX}/users/", headers=headers).status_code == 403
    assert client.get(f"{PREFIX}/access/me").status_code == 401


def test_grant_revoke_and_escalation(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    admin = superuser_token_headers
    headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    user_id = client.get(f"{PREFIX}/users/me", headers=headers).json()["id"]
    created = client.post(
        f"{PREFIX}/roles/", headers=admin, json={"name": f"reader-{uuid.uuid4().hex}"}
    )
    assert created.status_code == 200
    role = created.json()
    assert role["permissions"] == []
    policy = f"{PREFIX}/roles/{role['id']}/permissions"
    assignment = f"{PREFIX}/roles/users/{user_id}"
    for invalid in ["roles.manage", "unknown.view"]:
        assert (
            client.put(
                policy, headers=admin, json={"permissions": [invalid]}
            ).status_code
            == 422
        )
    assert (
        client.put(
            policy, headers=admin, json={"permissions": ["users.view"]}
        ).status_code
        == 200
    )
    assert (
        client.put(
            assignment, headers=headers, json={"role_ids": [role["id"]]}
        ).status_code
        == 403
    )
    assert (
        client.put(
            assignment, headers=admin, json={"role_ids": [str(uuid.uuid4())]}
        ).status_code
        == 422
    )
    assert (
        client.put(
            assignment, headers=admin, json={"role_ids": [role["id"]]}
        ).status_code
        == 200
    )
    assert client.get(f"{PREFIX}/users/", headers=headers).status_code == 200
    assert (
        client.patch(
            f"{PREFIX}/users/{user_id}", headers=headers, json={"is_superuser": True}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"{PREFIX}/users/",
            headers=headers,
            json={"email": random_email(), "password": "test-only-password"},
        ).status_code
        == 403
    )
    assert (
        client.put(policy, headers=headers, json={"permissions": []}).status_code == 403
    )
    assert (
        client.patch(
            f"{PREFIX}/users/me", headers=headers, json={"full_name": "denied"}
        ).status_code
        == 403
    )
    assert (
        client.put(policy, headers=admin, json={"permissions": []}).status_code == 200
    )
    assert client.get(f"{PREFIX}/users/", headers=headers).status_code == 403
    assert (
        client.get(f"{PREFIX}/access/me", headers=headers).json()["permissions"] == []
    )
    assert (
        client.put(assignment, headers=admin, json={"role_ids": []}).status_code == 200
    )
    assert (
        "profile.view"
        in client.get(f"{PREFIX}/access/me", headers=headers).json()["permissions"]
    )
    assert (
        client.put(
            assignment, headers=admin, json={"role_ids": [role["id"]]}
        ).status_code
        == 200
    )
    assert client.delete(f"{PREFIX}/users/{user_id}", headers=admin).status_code == 200


def test_default_policy_persists(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    admin = superuser_token_headers
    visitor = next(
        role
        for role in client.get(f"{PREFIX}/roles/", headers=admin).json()
        if role["name"] == "访客"
    )
    path = f"{PREFIX}/roles/{visitor['id']}/permissions"
    try:
        assert (
            client.put(path, headers=admin, json={"permissions": []}).status_code == 200
        )
        seed_permissions(db)
        assert (
            client.get(f"{PREFIX}/access/me", headers=normal_user_token_headers).json()[
                "permissions"
            ]
            == []
        )
    finally:
        assert (
            client.put(
                path, headers=admin, json={"permissions": visitor["permissions"]}
            ).status_code
            == 200
        )


def test_admin_immutable_and_unknown_denied(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    admin = superuser_token_headers
    identity = client.get(f"{PREFIX}/users/me", headers=admin).json()
    assert (
        client.put(
            f"{PREFIX}/roles/users/{identity['id']}",
            headers=admin,
            json={"role_ids": []},
        ).status_code
        == 403
    )
    assert all(
        page["allowed"]
        for page in client.get(f"{PREFIX}/access/me", headers=admin).json()["pages"]
    )
    user = db.get(User, uuid.UUID(identity["id"]))
    assert user is not None
    with pytest.raises(HTTPException) as error:
        check_permission(db, user, "unregistered.view")
    assert error.value.status_code == 403

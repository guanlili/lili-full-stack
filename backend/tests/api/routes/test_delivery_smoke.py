"""Exercise the deployment smoke protocol against real auth APIs in app_test."""

import importlib.util
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string


def test_authenticated_delivery_smoke(client: TestClient, db: Session) -> None:
    script = Path(__file__).resolve().parents[4] / "scripts/smoke_test.py"
    spec = importlib.util.spec_from_file_location("delivery_smoke", script)
    assert spec and spec.loader
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    email, password = random_email(), random_lower_string()
    crud.create_user(session=db, user_create=UserCreate(email=email, password=password))

    class Adapter:
        def request(
            self,
            path: str,
            expected: int,
            token: str = "",
            body: Any = None,
            form: bool = False,
        ) -> Any:
            if path == "/login":
                return b'<div id="root"></div>'
            headers = {"Authorization": f"Bearer {token}"} if token else None
            if body is None:
                response = client.get(path, headers=headers)
            elif form:
                response = client.post(path, data=body, headers=headers)
            else:
                response = client.post(path, json=body, headers=headers)
            assert response.status_code == expected, f"Smoke status mismatch: {path}"
            return response.json()

    smoke.run(
        Adapter(),
        {
            "SMOKE_ADMIN_EMAIL": settings.FIRST_SUPERUSER,
            "SMOKE_ADMIN_PASSWORD": settings.FIRST_SUPERUSER_PASSWORD,
            "SMOKE_VISITOR_EMAIL": email,
            "SMOKE_VISITOR_PASSWORD": password,
        },
    )

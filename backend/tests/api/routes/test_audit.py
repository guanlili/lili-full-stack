import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.core.config import settings
from app.models import AuditLog, User


def test_read_audit_logs_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    # superuser_token_headers 由真实登录产生，login.success 必在且带操作者邮箱
    assert any(item["action"] == "login.success" for item in data["data"])
    assert any(item["actor_email"] == settings.FIRST_SUPERUSER for item in data["data"])


def test_read_audit_logs_forbidden_for_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=normal_user_token_headers,
    )
    # 已登录但权限不足 → 403（不是 401）
    assert r.status_code == 403


def test_audit_log_filters(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    superuser = db.exec(
        select(User).where(col(User.email) == settings.FIRST_SUPERUSER)
    ).one()

    # 动作过滤：不存在的动作返回空集
    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
        params={"action": "no-such-action"},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 0
    assert r.json()["data"] == []

    # 模糊匹配 + 操作者过滤
    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
        params={"action": "login", "actor_user_id": str(superuser.id)},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert all("login" in item["action"] for item in body["data"])
    assert all(item["actor_user_id"] == str(superuser.id) for item in body["data"])

    # 资源类型过滤（先断言非空：all() 对空列表恒真，测不出"过滤失效"）
    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
        params={"resource_type": "session"},
    )
    assert r.status_code == 200
    assert r.json()["data"], "登录/登出必然产生 session 类审计，列表不应为空"
    assert all(item["resource_type"] == "session" for item in r.json()["data"])


def test_audit_log_actor_email_survives_user_deletion(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """actor_user_id 刻意非 FK：删除用户后审计行仍在，邮箱展示为 null。"""
    from app import crud
    from app.models import UserCreate
    from tests.utils.user import user_authentication_headers
    from tests.utils.utils import random_email, random_lower_string

    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    headers = user_authentication_headers(client=client, email=email, password=password)
    # 登录 + 登出产生带 actor 的审计
    assert (
        client.post(f"{settings.API_V1_STR}/login/logout", headers=headers).status_code
        == 200
    )

    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
        params={"actor_user_id": str(user.id), "limit": 200},
    )
    assert r.status_code == 200
    assert any(
        item["actor_email"] == email and item["action"] == "login.success"
        for item in r.json()["data"]
    )

    db.delete(user)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
        params={"actor_user_id": str(user.id), "limit": 200},
    )
    assert r.status_code == 200
    entries = r.json()["data"]
    assert entries, "删除用户后审计行必须保留"
    assert all(item["actor_email"] is None for item in entries)


def test_audit_log_pagination_bounds(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    for params in ({"skip": -1}, {"limit": 10_000}):
        r = client.get(
            f"{settings.API_V1_STR}/audit-logs/",
            headers=superuser_token_headers,
            params=params,
        )
        assert r.status_code == 422


def test_audit_written_in_independent_transaction(db: Session) -> None:
    """审计用独立连接提交：即使调用方事务回滚，已写审计不丢。"""
    from app.core.audit import record_audit

    user = db.exec(
        select(User).where(col(User.email) == settings.FIRST_SUPERUSER)
    ).one()
    record_audit(
        session=db,
        actor=user,
        action="test.independent_tx",
        resource_type="test",
    )
    # 调用方回滚自己的事务（模拟业务失败）
    db.rollback()

    check = Session(db.get_bind())
    try:
        rows = check.exec(
            select(AuditLog).where(col(AuditLog.action) == "test.independent_tx")
        ).all()
        assert rows, "审计已独立提交，不应随调用方回滚消失"
    finally:
        # 清理测试产生的行，避免影响其他用例
        for row in rows:
            check.delete(row)
        check.commit()
        check.close()


def test_audit_log_retention_prunes_expired_rows(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """配置保留期后，超管查看审计顺带清理过期行；窗口内的新鲜行保留。"""
    from datetime import UTC, datetime, timedelta

    monkeypatch.setattr(settings, "AUDIT_LOG_RETENTION_DAYS", 30)
    db.add(
        AuditLog(
            action="test.retention_old",
            resource_type="test",
            created_at=datetime.now(UTC) - timedelta(days=31),
        )
    )
    db.add(AuditLog(action="test.retention_fresh", resource_type="test"))
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
        params={"action": "test.retention"},
    )
    assert r.status_code == 200
    actions = [item["action"] for item in r.json()["data"]]
    assert "test.retention_old" not in actions
    assert "test.retention_fresh" in actions

from collections.abc import Generator
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.core.config import settings


def test_health_check_lightweight(client: TestClient) -> None:
    """存活检查：不依赖数据库，恒 200"""
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() is True


def test_ready_check_with_database(client: TestClient) -> None:
    """就绪检查：数据库可用时返回 200"""
    r = client.get(f"{settings.API_V1_STR}/utils/ready-check/")
    assert r.status_code == 200
    assert r.json() == {"message": "Ready"}


def test_ready_check_fails_when_db_down(client: TestClient) -> None:
    """就绪检查：数据库查询失败时返回 503，且不泄露内部异常细节"""

    class BrokenSession:
        """连接已建立但任何查询都失败（模拟 DB 半死/连接被回收）"""

        def __getattr__(self, name: str) -> object:
            def _fail(*_args: object, **_kwargs: object) -> object:
                raise RuntimeError(
                    "simulated: connection refused to db host 10.0.0.1:5432"
                )

            return _fail

    def broken_get_db() -> Generator[object]:
        yield BrokenSession()

    # 临时替换依赖；结束时恢复 conftest 设置的测试库 override（不能直接 pop）
    previous = client.app.dependency_overrides.get(get_db)
    client.app.dependency_overrides[get_db] = broken_get_db
    try:
        r = client.get(f"{settings.API_V1_STR}/utils/ready-check/")
        assert r.status_code == 503
        # detail 是固定文案，不包含异常信息
        assert r.json() == {"detail": "Service not ready"}
        assert "10.0.0.1" not in r.text
    finally:
        if previous is not None:
            client.app.dependency_overrides[get_db] = previous
        else:
            client.app.dependency_overrides.pop(get_db, None)


def test_recover_password_without_email_configured(client: TestClient) -> None:
    """找回密码：邮件未配置时不再 500，仍返回防枚举的成功文案，且不尝试发信"""
    with (
        patch("app.api.routes.login.settings") as mock_settings,
        patch("app.api.routes.login.send_email") as mock_send,
    ):
        mock_settings.emails_enabled = False
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery/{settings.FIRST_SUPERUSER}"
        )
        assert r.status_code == 200
        assert r.json() == {
            "message": "If that email is registered, we sent a password recovery link"
        }
        mock_send.assert_not_called()

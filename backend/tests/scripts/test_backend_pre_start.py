from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select

from app.backend_pre_start import init, logger, main


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock

    select1 = select(1)

    with (
        patch("app.backend_pre_start.Session", return_value=session_mock),
        patch("app.backend_pre_start.select", return_value=select1),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert connection_successful, (
            "The database connection should be successful and not raise an exception."
        )

        session_mock.exec.assert_called_once_with(select1)


def test_init_retries_then_reraises_on_failure() -> None:
    """探活失败时记录错误；原始函数向上抛出异常（重试策略由 tenacity 装饰器负责）。"""
    engine_mock = MagicMock()
    session_mock = MagicMock()
    session_mock.__enter__.return_value = session_mock
    session_mock.exec.side_effect = RuntimeError("db down")

    with (
        patch("app.backend_pre_start.Session", return_value=session_mock),
        patch("app.backend_pre_start.select", return_value=select(1)),
        patch.object(logger, "info", MagicMock()),
        patch.object(logger, "error", MagicMock()) as error_mock,
        patch.object(logger, "warn", MagicMock()),
        pytest.raises(RuntimeError, match="db down"),
    ):
        # 取 tenacity 包装前的原始函数，避免在测试里跑满 300 次重试等待
        init.__wrapped__(engine_mock)

    error_mock.assert_called_once()


def test_main_calls_init_with_engine() -> None:
    """main() 用全局 engine 探活并记录起止日志。"""
    with (
        patch("app.backend_pre_start.init") as init_mock,
        patch.object(logger, "info", MagicMock()) as info_mock,
    ):
        main()

    init_mock.assert_called_once()
    # 起止两条日志
    assert len(info_mock.call_args_list) == 2

import json
import logging

from app.core.logging import AccessJsonFormatter, JsonFormatter, configure_logging


def _record(
    name: str,
    msg: str,
    args: tuple[object, ...] | None = (),
    level: int = logging.INFO,
    extra: dict | None = None,
) -> logging.LogRecord:
    record = logging.LogRecord(name, level, "test.py", 1, msg, args, None)
    if extra:
        record.__dict__.update(extra)
    return record


def test_json_formatter_flattens_extra_fields() -> None:
    """普通业务日志：extra 扁平进 JSON，保留标准字段。"""
    record = _record(
        "app.main",
        "request",
        extra={"request_id": "abc", "status": 200, "latency_ms": 8.5},
    )
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.main"
    assert payload["message"] == "request"
    assert payload["request_id"] == "abc"
    assert payload["status"] == 200
    assert payload["latency_ms"] == 8.5
    # 保留属性不泄漏进 payload
    assert "args" not in payload
    assert "lineno" not in payload


def test_access_formatter_parses_uvicorn_args() -> None:
    """uvicorn.access：位置参数拆成 method/path/status 等结构化字段。"""
    args = ("127.0.0.1:52440", "GET", "/api/v1/utils/ready-check/", "1.1", 200)
    record = _record("uvicorn.access", '%s - "%s %s HTTP/%s" %s', args)
    payload = json.loads(AccessJsonFormatter().format(record))
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/utils/ready-check/"
    assert payload["status"] == 200
    assert payload["client_addr"] == "127.0.0.1:52440"
    assert payload["http_version"] == "1.1"
    # 原始 args 不进入 JSON
    assert "args" not in payload


def test_access_formatter_without_uvicorn_args_falls_back() -> None:
    """非五元组记录（如手动 emit）不报错，按普通 JSON 处理。"""
    record = _record("uvicorn.access", "manual message")
    payload = json.loads(AccessJsonFormatter().format(record))
    assert payload["message"] == "manual message"
    assert "method" not in payload


def test_configure_logging_is_idempotent_and_wires_uvicorn() -> None:
    """重复调用不重复挂 handler；uvicorn 子 logger 接 JSON handler 且不向上传播。"""
    configure_logging()
    configure_logging()

    root = logging.getLogger()
    assert len(root.handlers) == 1

    access = logging.getLogger("uvicorn.access")
    error = logging.getLogger("uvicorn.error")
    assert len(access.handlers) == 1
    assert len(error.handlers) == 1
    assert access.propagate is False
    assert error.propagate is False
    assert isinstance(access.handlers[0].formatter, AccessJsonFormatter)
    assert isinstance(error.handlers[0].formatter, JsonFormatter)

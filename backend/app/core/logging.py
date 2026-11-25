import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """结构化 JSON 日志：字段扁平、可直接被采集器解析；消息体不夹带路径参数。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # 业务上下文（request_id / path / status / latency_ms 等）通过 extra 传入
        for key, value in record.__dict__.items():
            if key in _RESERVED_ATTRS or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_RESERVED_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


class AccessJsonFormatter(JsonFormatter):
    """uvicorn.access 专用：把访问日志的位置参数拆成结构化字段。

    uvicorn 访问记录的 `record.args` 为
    `(client_addr, method, full_path, http_version, status_code)`；
    这里在 JSON 输出前把它们摊平到 payload，消息体只保留访问行摘要。
    """

    def format(self, record: logging.LogRecord) -> str:
        args = record.args
        if isinstance(args, tuple) and len(args) == 5:
            client_addr, method, full_path, http_version, status_code = args
            # 先按原模板取格式化后的消息，再摊平字段并清空 args，避免基类重复序列化
            record.message = record.getMessage()
            record.__dict__.update(
                {
                    "client_addr": client_addr,
                    "method": method,
                    "path": full_path,
                    "http_version": http_version,
                    "status": int(str(status_code)),
                }
            )
            record.args = ()
        return super().format(record)


def configure_logging() -> None:
    """统一结构化 JSON 日志（幂等：root 已有 handler 时不重复配置）。

    uvicorn 自身的 access / error / asgi 日志也挂到同一 JSON handler 并关闭向上传播，
    避免框架默认的纯文本访问日志（`INFO: 127.0.0.1 - "GET ..."`）与应用 JSON 日志并存。
    应用中间件已记录带 request_id / latency_ms 的结构化 request 日志，uvicorn.access
    仅作为兜底访问记录，字段映射到标准 JSON 结构。
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # uvicorn 子 logger 复用 root 的 JSON handler；propagate=False 防止再走一遍 root 造成重复输出
    for name in ("uvicorn", "uvicorn.error", "uvicorn.asgi"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
        uv_logger.setLevel(logging.INFO)
        uv_logger.propagate = False

    # access 日志参数结构不同，单独挂专用 formatter
    access_handler = logging.StreamHandler()
    access_handler.setFormatter(AccessJsonFormatter())
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False

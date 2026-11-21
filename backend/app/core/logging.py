import logging


def configure_logging() -> None:
    """统一应用日志格式（幂等：root 已有 handler 时 basicConfig 不重复配置）。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

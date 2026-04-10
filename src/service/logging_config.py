"""Logging configuration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger


class FlowBridgeJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter with stable keys for tracing."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record.setdefault("workflow_id", getattr(record, "workflow_id", None))
        log_record.setdefault("execution_id", getattr(record, "execution_id", None))


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application-wide JSON logging."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = FlowBridgeJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")

    root_handler = logging.StreamHandler()
    root_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [root_handler]

    for logger_name in ("uvicorn", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_handler = logging.StreamHandler()
        uvicorn_handler.setFormatter(formatter)
        uvicorn_logger.setLevel(level)
        uvicorn_logger.handlers = [uvicorn_handler]
        uvicorn_logger.propagate = False

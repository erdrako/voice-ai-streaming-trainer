import json
import logging
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    """
    Small JSON log formatter.

    Production-oriented improvement:
    Structured logs are easier to search and aggregate than plain strings.
    This keeps the training app dependency-light while showing the concept.

    Expansion point:
    Replace this with structlog, loguru, OpenTelemetry logs, or a cloud logging
    adapter without changing application use cases.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "session_id"):
            payload["session_id"] = record.session_id
        if hasattr(record, "event_type"):
            payload["event_type"] = record.event_type
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """
    Configure process-wide JSON logging.

    This belongs near infrastructure/cross-cutting code because logging is not a
    domain concern. It is configured from `main.py` during app bootstrap.
    """

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

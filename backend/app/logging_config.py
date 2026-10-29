import json
import logging
from datetime import UTC, datetime

from app.config import get_settings
from app.request_context import get_request_id


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id

        structured_fields = (
            "source_id",
            "collection_attempt_id",
            "evidence_id",
            "collection_status",
            "failure_code",
            "evidence_created",
        )

        for field_name in structured_fields:
            value = getattr(record, field_name, None)

            if value is not None:
                payload[field_name] = value

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    settings = get_settings()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)

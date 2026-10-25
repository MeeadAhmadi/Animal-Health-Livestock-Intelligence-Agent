import json
import logging

from app.logging_config import JsonFormatter


def test_json_formatter_includes_collection_trace_fields() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="app.collection",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Collection completed",
        args=(),
        exc_info=None,
    )

    record.source_id = 12
    record.collection_attempt_id = 34
    record.evidence_id = 56
    record.collection_status = "succeeded"
    record.failure_code = None
    record.evidence_created = True

    payload = json.loads(formatter.format(record))

    assert payload["source_id"] == 12
    assert payload["collection_attempt_id"] == 34
    assert payload["evidence_id"] == 56
    assert payload["collection_status"] == "succeeded"
    assert payload["evidence_created"] is True
    assert "failure_code" not in payload

from __future__ import annotations
import logging
from .request_storage import get_request

class RequestContextFilter(logging.Filter):
    """
    Добавляет в запись лога данные запроса (request_id, user, path, method),
    если мы в веб-контексте. В фоновом контексте оставляет дефолты.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        req = get_request()
        if req is not None:
            record.request_id = getattr(req, "request_id", "-")
            user = getattr(req, "user", None)
            record.user = (
                getattr(user, "email", "-") if getattr(user, "is_authenticated", False) else "-"
            )
            record.path = getattr(req, "path", "-")
            record.method = getattr(req, "method", "-")
        else:
            record.request_id = getattr(record, "request_id", "-")
            record.user = getattr(record, "user", "-")
            record.path = getattr(record, "path", "-")
            record.method = getattr(record, "method", "-")
        return True
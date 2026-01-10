from __future__ import annotations

import logging

from .request_storage import get_request


class RequestContextFilter(logging.Filter):
    """Добавляет в запись лога данные запроса (request_id, user_email, path, method).

    Работает как в web-контексте (через middleware + threadlocal),
    так и в фоновом контексте (tasks / tests / management commands),
    гарантируя наличие всех полей, используемых форматтером.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # --- дефолты (важно: форматтер никогда не должен падать) ---
        record.request_id = getattr(record, "request_id", "-")
        record.user_email = getattr(record, "user_email", "-")
        record.path = getattr(record, "path", "-")
        record.method = getattr(record, "method", "-")

        # для обратной совместимости (если где-то использовался record.user)
        record.user = getattr(record, "user", record.user_email)

        # --- web-контекст ---
        req = get_request()
        if req is not None:
            record.request_id = getattr(req, "request_id", record.request_id)

            user = getattr(req, "user", None)
            if getattr(user, "is_authenticated", False):
                record.user_email = getattr(user, "email", record.user_email)
            else:
                record.user_email = "-"

            record.user = record.user_email
            record.path = getattr(req, "path", record.path)
            record.method = getattr(req, "method", record.method)

        return True

from __future__ import annotations

import uuid
from django.utils.deprecation import MiddlewareMixin

from .request_storage import set_request, clear_request


class CurrentRequestMiddleware(MiddlewareMixin):
    """Кладёт текущий request в thread-local, проставляет request_id
    и дублирует его в заголовок ответа X-Request-ID."""

    inbound_header = "HTTP_X_REQUEST_ID"  # если прокси присылает внешний RID
    outbound_header = "X-Request-ID"

    def process_request(self, request):
        set_request(request)
        rid = request.META.get(self.inbound_header) or uuid.uuid4().hex[:12]
        request.request_id = rid

        user = getattr(request, "user", None)
        request.user_email = (
            getattr(user, "email", "-")
            if getattr(user, "is_authenticated", False)
            else "-"
        )

    def process_response(self, request, response):
        rid = getattr(request, "request_id", "-") if request is not None else "-"
        response[self.outbound_header] = rid
        clear_request()
        return response

    def process_exception(self, request, exception):
        clear_request()
        # вернём None — пусть стандартная обработка исключения продолжится

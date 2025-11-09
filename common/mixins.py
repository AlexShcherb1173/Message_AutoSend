from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.http import HttpRequest, HttpResponseNotModified
from django.utils.http import http_date, parse_http_date_safe

from .request_storage import get_request


class ClientCacheMixin:
    """
    Добавляет Cache-Control/Last-Modified к ответу и корректно обрабатывает
    Conditional GET (If-Modified-Since) — отдаёт 304, если контент не менялся.

    Наследники могут переопределить get_last_modified() и/или cache_seconds/private.
    """
    cache_seconds: int = 120  # 2 минуты по умолчанию
    cache_private: bool = True

    def get_last_modified(self) -> Optional[datetime]:
        """
        Верни datetime последнего изменения данных для страницы.
        Если None — Last-Modified не выставляем и 304 не используем.
        """
        return None

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        # Стандартное клиентское кеширование
        response["Cache-Control"] = f'{"private" if self.cache_private else "public"}, max-age={self.cache_seconds}'

        last_modified = self.get_last_modified()
        if last_modified:
            # Учитываем Conditional GET: If-Modified-Since
            request: Optional[HttpRequest] = getattr(self, "request", None)
            if request is not None:
                ims_header = request.META.get("HTTP_IF_MODIFIED_SINCE")
                if ims_header:
                    ims_ts = parse_http_date_safe(ims_header)
                    if ims_ts is not None:
                        # сравниваем по секундам
                        if int(last_modified.timestamp()) <= int(ims_ts):
                            not_modified = HttpResponseNotModified()
                            not_modified["Cache-Control"] = response["Cache-Control"]
                            not_modified["Last-Modified"] = http_date(last_modified.timestamp())
                            return not_modified

            response["Last-Modified"] = http_date(last_modified.timestamp())

        return response


# === Хелперы контекста запроса для логов/отчётов ===

def get_request_id(default: str = "-") -> str:
    """
    Возвращает request_id, который проставляет CurrentRequestMiddleware.
    В не-веб контексте (manage-команды, фоновые задачи) вернёт default.
    """
    req = get_request()
    return getattr(req, "request_id", default) if req is not None else default


def get_current_user_email(default: str = "-") -> str:
    """
    Возвращает email текущего пользователя, если он аутентифицирован.
    В не-веб контексте или для анонимных — default.
    """
    req = get_request()
    if req is not None:
        user = getattr(req, "user", None)
        if getattr(user, "is_authenticated", False):
            return getattr(user, "email", default) or default
    return default
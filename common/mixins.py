from datetime import datetime
from typing import Optional
from django.utils.http import http_date

class ClientCacheMixin:
    """
    Добавляет Cache-Control/Last-Modified заголовки к ответу.
    Применяем на списках/отчётах, чтобы браузер корректно делал 304.
    """
    cache_seconds: int = 120  # 2 минуты по умолчанию
    cache_private: bool = True

    def get_last_modified(self) -> Optional[datetime]:
        """
        Переопредели в наследниках. Должна вернуть dt последнего обновления данных.
        Если None — Last-Modified не выставляем.
        """
        return None

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Cache-Control"] = f'{"private" if self.cache_private else "public"}, max-age={self.cache_seconds}'
        lm = self.get_last_modified()
        if lm:
            response["Last-Modified"] = http_date(lm.timestamp())
        return response
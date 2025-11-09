from __future__ import annotations
import threading
from typing import Optional
from django.http import HttpRequest

_request_local = threading.local()

def set_request(request: Optional[HttpRequest]) -> None:
    _request_local.request = request

def get_request() -> Optional[HttpRequest]:
    return getattr(_request_local, "request", None)

def clear_request() -> None:
    if hasattr(_request_local, "request"):
        delattr(_request_local, "request")
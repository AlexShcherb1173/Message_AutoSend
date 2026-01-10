from django.test import TestCase, RequestFactory
from django.http import HttpResponse

from common.middleware import CurrentRequestMiddleware


class CurrentRequestMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mw = CurrentRequestMiddleware(get_response=lambda r: HttpResponse("ok"))

    def test_sets_request_id_and_response_header(self):
        req = self.factory.get("/")
        resp = self.mw(req)
        self.assertIn("X-Request-ID", resp)
        self.assertTrue(len(resp["X-Request-ID"]) >= 6)
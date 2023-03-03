from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class TestPingdomHealthCheckView(TestCase):
    @patch("v2_api_client.library.healthcheck.get_status")
    def setUp(self, mocked_healthcheck_client) -> None:
        mocked_healthcheck_client.return_value = "OK"
        self.response = self.client.get(reverse("pingdom_healthcheck"))

    def test_view_url_returns_status_code_200(self):
        self.assertEqual(self.response.status_code, 200)

    @patch("v2_api_client.library.healthcheck.get_status")
    def test_view_url_returns_status_code_503(self, mocked_healthcheck_client):
        mocked_healthcheck_client.return_value = "error"
        response = self.client.get(reverse("pingdom_healthcheck"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.response.headers["Content-Type"], "text/xml")

    def test_view_url_headers(self):
        self.assertEqual(self.response.headers["Content-Type"], "text/xml")
        self.assertEqual(self.response.headers["Cache-Control"], "no-store")

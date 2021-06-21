from django.test import TestCase, override_settings

from core.utils import (
    internal_redirect,
)


class UtilsTestCases(TestCase):
    @override_settings(ALLOWED_HOSTS=['trade-remedies.com',])
    def internal_redirect(self):
        test_redirect = internal_redirect(
            "https://trade-remedies.com/test",
            "/dashboard/",
        )

        assert test_redirect.url == "https://trade-remedies.com/test"

        test_redirect = internal_redirect(
            "https://www.google.com/?test=1",
            "/dashboard/",
        )

        assert test_redirect.url == "/dashboard/"

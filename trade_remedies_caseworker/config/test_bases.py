from django.test import TestCase

from tests.models import TestUser


class UserTestBase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.test_user = TestUser.objects.create_user(
            username="test",
            email="test@example.com",
            password="test_password",
        )

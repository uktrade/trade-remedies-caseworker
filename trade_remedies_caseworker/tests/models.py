from django.contrib.auth.models import AbstractUser


class TestUser(AbstractUser):
    __test__ = False

    @staticmethod
    def has_group(groups):
        return True

    def has_perms(self, permissions):
        return True

    def has_perm(self, permission):
        return True

    @property
    def token(self):
        return "test_token"

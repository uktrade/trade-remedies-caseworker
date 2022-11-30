from django.contrib.auth.models import AbstractUser


class TestUser(AbstractUser):
    def has_group(self, groups):
        return True

    def has_perms(self, permissions):
        return True

    def has_perm(self, permission):
        return True

    @property
    def token(self):
        return "test_token"

from django.contrib.auth.models import User
from trade_remedies_client.client import Client


class TransientUser(User):
    def has_group(self, groups):
        if not isinstance(groups, list):
            groups = [groups]
        return any([grp in self.groups for grp in groups])


class AuthenticationBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        response_data = Client().authenticate(username, password)
        if response_data and response_data.get("token"):
            request.session["token"] = response_data["token"]
            request.session["user"] = response_data["user"]
        # TODO Fix undefind 'email'
        user = TransientUser(username=email, token=response_data["token"])  # noqa: F821
        user.is_authenticated = True
        user.backend = self
        user.groups = response_data["groups"]
        return user

    def has_perm(self, perm, **kwargs):
        return True

    def get_user(self, user_id):
        try:
            return TransientUser()
        except Exception:
            return None

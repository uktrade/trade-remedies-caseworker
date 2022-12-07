"""
auth.py: Caseworker client authentication.
"""
from django.contrib.auth.models import User
from trade_remedies_client.client import Client


class TransientUser(User):
    def has_group(self, groups):
        if isinstance(groups, str):
            groups = [groups]
        return any([grp in self.groups for grp in groups])


class AuthenticationBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        rd = Client().authenticate(username, password)
        if rd and rd.get("token"):
            request.session["token"] = rd["token"]
            request.session["user"] = rd["user"]
        # If the following F821 suppression is legitimate, please indicate in
        # a replacement for this comment how executing the code avoids
        # raising a NameError exception.
        user = TransientUser(username=email, token=rd["token"])  # noqa: F821
        user.is_authenticated = True
        user.backend = self
        user.groups = rd["groups"]
        return user

    def has_perm(self, perm, **kwargs):
        return True

    def get_user(self, user_id):
        try:
            return TransientUser()
        except Exception:
            return None

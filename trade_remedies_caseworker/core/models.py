from .constants import SECURITY_GROUPS_TRA_ADMINS, SECURITY_GROUPS_TRA_TOP_ADMINS


class TransientUser:
    """
    A TransientUser object mimics a Django auth User but does not
    persist anywhere. Insetad it is created on the fly by the
    APIUserMiddleware middleware using session data.
    """

    def __init__(self, **kwargs):
        self.is_authenticated = True
        self.transient_user = True
        self.permissions = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    def has_group(self, groups):
        if not isinstance(groups, list):
            groups = [groups]
        return any([grp in self.groups for grp in groups])

    def has_perms(self, permissions):
        return any([prm in self.permissions for prm in permissions])

    def has_perm(self, permission):
        return permission in self.permissions

    @property
    def is_admin(self):
        return any([grp in self.groups for grp in SECURITY_GROUPS_TRA_ADMINS])

    @property
    def is_top_admin(self):
        """
        To resolve TR-2639, adding this check for higher admin access. 
        This is because lead inv. is considered admin currently. This can be changed
        but the implications are not clear.
        """
        return any([grp in self.groups for grp in SECURITY_GROUPS_TRA_TOP_ADMINS])

    def reload(self, request):
        """
        Reload the user from the API
        """
        user = get_user(request.user.token, self.id)
        request.session["user"] = user
        request.session.modified = True
        self.init_fields(**user)
        return user

import logging

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin


logger = logging.getLogger(__name__)


class GroupRequiredMixin(AccessMixin):
    """Verify that the current user is a member of a group."""
    groups_required = None
    super_user = 'Super User'

    def get_group_required(self):
        """
        Override this method to override the groups_required attribute.
        Must return an iterable.
        """
        if self.groups_required is None:
            raise ImproperlyConfigured(
                '{0} is missing the groups_required attribute. Define {0}.groups_required, or override '
                '{0}.get_groups_required().'.format(self.__class__.__name__)
            )
        if isinstance(self.groups_required, str):
            groups = (self.groups_required,)
        else:
            groups = self.groups_required
        return groups

    def has_group(self):
        """
        Override this method to customize the way groups are checked.
        """
        groups = self.get_group_required()
        return self.request.user.has_group(self.super_user) or self.request.user.has_group(groups)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_group():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class FeatureFlags(TradeRemediesAPIClientMixin):
    """
    Maintains a cache of feature flag values.
    """
    def __init__(self, request):
        self._flag_map = {}
        self.request = request

    def __call__(self, name):
        try:
            return self._flag_map[name]
        except KeyError:
            val = self.client(self.request.user).is_feature_flag_enabled(name)
            self._flag_map[name] = val
            return val


class FeatureFlagMixin(object):
    """
    Adds a `feature_flags` object to the view which will cache any feature
    flags requested for the lifetime of the request.

    Example usage within a View:

    def post(self, request):
        if self.feature_flags('my_flag'):
            # some conditional behaviour.
    """
    def dispatch(self, request, *args, **kwargs):
        self.feature_flags = FeatureFlags(request)
        return super().dispatch(request, *args, **kwargs)

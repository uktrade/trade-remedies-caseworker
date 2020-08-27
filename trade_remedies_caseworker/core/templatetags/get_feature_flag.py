from core.templatetags import register
from trade_remedies_client.client import Client

"""
Template tag to fetch the value of a feature flag defined in the system
parameters.

Note: The key passed to the tag should omit the "FEATURE_" prefix defined
on the key in the corresponding system parameter.

Usage:
    {% get_feature_flag "MY_FLAG" as FEATURE_MY_FLAG %}
    {% if FEATURE_MY_FLAG %}
        <div>Some feature...</div>
    {% endif %}
"""


@register.simple_tag(takes_context=True)
def get_feature_flag(context, key):
    return Client(context['user'].token).is_feature_flag_enabled(key)

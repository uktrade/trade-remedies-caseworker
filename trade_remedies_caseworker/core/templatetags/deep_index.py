from core.templatetags import register
from core.utils import deep_index_items_by


@register.filter
def deep_index(items, key):
    """
    Perform a deep indexing operation on a list of dict items
    """
    return deep_index_items_by(items, key)

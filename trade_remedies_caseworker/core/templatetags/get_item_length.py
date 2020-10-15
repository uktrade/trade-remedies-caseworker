from core.templatetags import register


@register.filter
def get_item_length(obj, key):
    """
    Template tag to return the length of item in gien dictionary
    """
    val = "0"
    if obj and type(obj) == dict:
        val = len(obj.get(key, []))
    return val

from core.templatetags import register
from django.utils.safestring import mark_safe
import datetime

"""
Template tag to display a formatted date given an iso date string
Usage:
    {% format_date datestr %}
"""


@register.simple_tag
def format_date(date, format_str="%d %b %Y %H:%M:%S", wrapped=True):
    if isinstance(date, str) and len(date) > 18:
        _timeless = datetime.datetime.strptime(date[:19], "%Y-%m-%dT%H:%M:%S")
        _formatted = datetime.datetime.strftime(_timeless, format_str)
        _full = datetime.datetime.strftime(_timeless, "%d %b %Y %H:%M:%S")
        if wrapped and _full != _formatted:
            return mark_safe(f"<span title='{_full}'>{_formatted}</span>")
        return mark_safe(_formatted)
    return "n/a"

from core.templatetags import register
from django.utils.safestring import mark_safe
import datetime

"""
Pass in an iso date and the tag outputs a warning icon if the date is in the past

"""

@register.simple_tag
def overdue_warning(date):
    if isinstance(date, str) and len(date) > 18:
        date = datetime.datetime.strptime(date[:19], "%Y-%m-%dT%H:%M:%S")
        if datetime.datetime.now() > date:
        	return mark_safe('<div class="icon icon-amber-warning"></div>')
    return ''

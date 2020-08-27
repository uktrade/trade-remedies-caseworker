from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display an ascii character
Usage:
    {{ ascii code }}

"""


@register.simple_tag
def ascii(code):
    html = f"""&#{code};"""
    return mark_safe(html)

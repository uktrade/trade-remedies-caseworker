from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display a number in a circle
Usage:
    {% number_blob <number> %}
"""


@register.simple_tag
def number_blob(number):
    if not number:
        return ""
    output = ""
    return mark_safe('<div class="number-circle">' + str(number) + "</div>")

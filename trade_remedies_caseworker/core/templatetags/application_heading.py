from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display the title of the application

"""


@register.simple_tag
def application_heading():
    return mark_safe("Trade remedies investigation service")

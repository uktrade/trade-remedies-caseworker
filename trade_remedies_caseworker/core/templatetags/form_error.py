from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display an indicator for confidential or non confidential document
Usage:
    {% confidential confidential_boolean %}
"""

@register.simple_tag
def form_error(key, errors=None):
    errors = errors or {}
    if key in errors:
        if isinstance(errors[key], list):
            message = ''.join([
                f'<span id="{key}_error" class="error-message">{msg}</span>'
                for msg in errors[key]
            ])
            return mark_safe(message)
        else:
            return mark_safe(f'<span id="{key}_error" class="error-message">{errors[key]}</span>')
    return ''

@register.simple_tag
def form_group_error(key, errors=None):
    # this is the class to go in a form-group to indicate error
    if key in errors:
            return mark_safe('form-group-error')
    return ''


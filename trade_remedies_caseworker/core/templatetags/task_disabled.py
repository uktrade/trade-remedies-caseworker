from core.templatetags import register

"""
Template tag to evaluate the disabled property of an input tag.
Usage:
    {% task_disabled user task %}
"""


@register.simple_tag
def task_disabled(user, task):
    active = task.get('active', True)
    permission = task.get('permission')

    if permission:
        is_enabled = active and user.has_perm(permission)
    elif active:
        is_enabled = True
    else:
        is_enabled = False

    if is_enabled:
        return ''
    else:
        return 'disabled="disabled"'

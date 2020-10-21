from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display a link - if the given path is different from the current url -
or a simple span otherwise
Usage:
    {% link_or_not <title> <path> %}
"""


@register.simple_tag(takes_context=True)
def link_or_not(context, title, path):
    request = context.get("request")
    target = request.build_absolute_uri(path)
    if target == request.build_absolute_uri(request.path):
        return mark_safe(f"<span>{title}</span>")
    else:
        return mark_safe(f"""<a href="{target}">{title}</a>""")

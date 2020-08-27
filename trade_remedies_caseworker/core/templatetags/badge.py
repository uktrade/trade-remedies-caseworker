from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display a two letter badge to denote a case type
Usage:
    {{ case_type_badge case.type }}

"""


@register.simple_tag
def badge(content, alt_text=None, colour=None):
    colour = colour or 'black'
    if content:
        colour_style = f'style="background: {colour};"' if colour else ''
        badge = f"""<div class="circular-badge" {colour_style} title="{alt_text}">{content}</div>"""
        return mark_safe(badge)
    else:
        return ''

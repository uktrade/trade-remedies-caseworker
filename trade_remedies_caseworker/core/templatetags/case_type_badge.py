from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display a two letter badge to denote a case type
Usage:
    {{ case_type_badge case.type }}

"""


@register.simple_tag
def case_type_badge(case_type):
    if case_type:
        badge = f"""<div class="circular-badge" style="background: {case_type['colour']};" title="{case_type['name']}">{case_type['acronym']}</div>"""     # noqa: E501
        return mark_safe(badge)
    else:
        return "N/A"

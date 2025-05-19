from core.templatetags import register


@register.simple_tag
def page_range(total, start=1, end=None):
    """
    Return a range of integers for pagination.

    Usage:
        {% page_range total start end as range %}
        {% for i in range %}
            {{ i }}
        {% endfor %}
    """
    if end is None:
        end = int(total)

    return range(int(start), min(int(end) + 1, int(total) + 1))

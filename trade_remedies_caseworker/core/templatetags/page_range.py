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
    try:
        total = int(total)
        start = int(start)
        if end is None:
            end = total
        else:
            end = int(end)

        # Make sure start and end are within valid range
        start = max(1, start)
        end = min(total, end)

        # Make sure end is inclusive by adding 1 to range
        return list(range(start, end + 1))
    except (ValueError, TypeError):
        return []

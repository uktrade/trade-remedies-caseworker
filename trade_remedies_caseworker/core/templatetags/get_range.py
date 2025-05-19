from core.templatetags import register

@register.simple_tag
def get_range(total, start=1, end=None):
    """
    Return a range of numbers for pagination.
    Usage:
        {% for i in total|get_range:start,end %}
            {{ i }}
        {% endfor %}
        
    Example:
        {% for i in 10|get_range:1,5 %}
            {{ i }}  # outputs 1,2,3,4,5
        {% endfor %}
    """
    if end is None:
        end = total + 1
    return range(int(start), min(int(end) + 1, int(total) + 1))

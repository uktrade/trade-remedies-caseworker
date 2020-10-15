from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display the heading in a sortable table.

title = title, 
key = sort key
qstr = other query string parameters excluding the trailing '&'
asc for ascending sort

"""


@register.simple_tag
def table_heading(title, key, sort, tab=None, dir="asc"):
    active = sort == key
    active_str = " active" if active else ""
    current_dir = dir if active else "asc"
    next_dir_str = ("desc" if dir == "asc" else "asc") if active else current_dir
    return mark_safe(f'<th scope="col"><span class="pull-left">{title}</span></th>')

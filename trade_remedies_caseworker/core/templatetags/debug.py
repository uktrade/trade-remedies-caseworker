from core.templatetags import register
import json
from django.utils.safestring import mark_safe

"""
A template filter to display data in JSON format - useful when debugging the UI.

Usage: 
    {% data|to_json %}
"""

@register.filter
def debug(data):
	value = json.dumps(data, sort_keys=True, indent=4).replace('\'','&#39;')
	return mark_safe(f'<textarea>{value}</textarea>')

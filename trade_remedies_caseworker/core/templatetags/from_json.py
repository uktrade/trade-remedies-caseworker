from core.templatetags import register
import json

"""
Returns true if the provided path matches the path we are on

"""


@register.simple_tag()
def from_json(json_text):
    try:
        return json.loads(json_text)
    except Exception as ex:
        print(ex)
        pass
    return None

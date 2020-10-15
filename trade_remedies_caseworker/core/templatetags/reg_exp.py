from core.templatetags import register
import re


@register.simple_tag
def reg_exp(regex, str):
    """
    Does a regexp match on the given string and returns the match
    """
    return re.match(regex, str)

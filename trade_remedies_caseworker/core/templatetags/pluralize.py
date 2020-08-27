from core.templatetags import register

"""
Template tag to add a plural.  
By default if value == 1 returns '' otherwise 's'
Usage:
    {% pluralize <value> [<string if 1> <string if several>]%}

"""


@register.simple_tag
def pluralize(value, if_one=None, if_several=None):
    if int(value) == 1:
        return if_one if if_one != None else ''
    return if_several if if_several != None else 's'

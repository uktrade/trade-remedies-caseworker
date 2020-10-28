from core.templatetags import register
from core.utils import get
from django.utils.safestring import mark_safe
import datetime
from django.utils import timezone


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter
def _not(arg1):
    """Boolean or"""
    return not arg1


@register.filter
def _or(arg1, arg2):
    """Boolean or"""
    return arg1 or arg2


@register.filter
def _and(arg1, arg2):
    """Boolean and"""
    return arg1 and arg2


@register.filter
def _equals(arg1, arg2):
    """Returns true if arg1 equals arg2"""
    return (arg1 == arg2) or (str(arg1) == str(arg2))


@register.filter
def _notequals(arg1, arg2):
    """Returns true if arg1 and arg2 are not the same"""
    return arg1 != arg2


@register.filter
def _captalize(arg1):
    """Returns the string with an initial capital"""
    return str(arg1).captalize()


@register.filter
def _plus(arg1, arg2):
    """int plus"""
    return str(int(arg1) + int(arg2))


@register.filter
def _get(arg1, arg2):
    """get a value from an object"""
    return get(arg1, str(arg2))


@register.filter
def _int(arg1):
    """get a value from an object"""
    return int(arg1)


def suffix(d):
    return "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")


@register.filter
def format_date(date_str, format_str="%d %b %Y"):
    if isinstance(date_str, str) and len(date_str) > 18:
        date = datetime.datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        out = date.strftime(format_str).replace("{S}", str(date.day) + suffix(date.day))
        time = date.strftime("%d %b %Y %H:%M:%S")
        if out != time:
            return mark_safe(f'<span title="{time}">{out}</span>')
        return mark_safe(f"{out}")
    return "n/a"

@register.filter
def format_date_no_span(date_str, format_str="%d %b %Y"):
    if isinstance(date_str, str) and len(date_str) > 18:
        date = datetime.datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        out = date.strftime(format_str).replace('{S}', str(date.day) + suffix(date.day))
        time = date.strftime('%d %b %Y %H:%M:%S')
        if out != time:
            return mark_safe(f'{out}')
        return mark_safe(f'{out}')
    return 'n/a'

@register.filter
def _find(value, in_string):
    """ true if the value is in the string """
    str_value = str(value)
    return in_string.find(str_value) > -1


@register.filter
def _multi_line(in_string):
    """ true if string has any linefeeds """
    return "\n" in str(in_string)


@register.filter
def add_days(date, days):
    """ add integer days to date """
    days = int(days or 0)
    if isinstance(date, str) and len(date) > 18:
        date = datetime.datetime.strptime(date[:19], "%Y-%m-%dT%H:%M:%S")
        return mark_safe((date + timezone.timedelta(days)).strftime("%Y-%m-%dT%H:%M:%S"))
    return "n/a"


@register.filter
def now(dummy):
    return mark_safe(timezone.now().strftime("%Y-%m-%dT%H:%M:%S"))


@register.filter
def split(str):
    return str.split()


@register.filter
def splitlines(str):
    return (str or "").splitlines()

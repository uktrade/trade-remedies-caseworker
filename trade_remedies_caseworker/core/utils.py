from datetime import datetime
from dateutil.parser import parse
import dpath
import logging
import json
import markdown
import re

from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import is_safe_url

from trade_remedies_client.exceptions import APIException

logger = logging.getLogger(__name__)


def deep_index_items_by(items, key):
    """
    Index a list of dicts by a given key.
    Returns a dict of the arrays of items based on the value of `key` in each item.
    """
    index = {}
    for item in items or []:
        try:
            index_key = str((dpath.util.get(item, key) or "")).lower()
        except KeyError:
            # NOTE: on key missing, this indexes as '', same as a None value.
            index_key = ""
        index.setdefault(index_key, [])
        index[index_key].append(item)

    return index


def deep_index_items_by_exists(items, key):
    """
    Index a list of dicts by whether a key is present or not.
    Returns a dict of the arrays of items with elements ['true'] and ['false']
    """
    index = {"true": [], "false": []}
    for item in items or []:
        index_key = None
        try:
            index_key = dpath.util.get(item, key) and "true"
        except KeyError:
            pass
        index[index_key or "false"].append(item)

    return index


def deep_update(target, source):
    """
    Deep merge two dicts
    """
    if isinstance(source, dict):
        for key, item in source.items():
            if key in target:
                target[key] = deep_update(target[key], item)
            else:
                target[key] = source[key]
    return target


def get(item, key, default=None):
    """
    Safe get to find a value based on a path
    """
    val = default
    try:
        val = dpath.util.get(item, key)
    except KeyError:
        pass
    return val


def key_by(items, key, children_key=False):
    """
    Index a list of dicts by the value of given key - forced to lowercase.
    Set child_key to say 'children' to recurse down a tree with 'children' attributes on nodes.
    """
    index = {}

    def inner(items, parent_key=None):
        for item in items:
            if parent_key:
                item["parent_key"] = parent_key
            _item_key = item[key] if isinstance(item[key], int) else item[key].lower()
            index[_item_key] = item
            if item.get(children_key):
                inner(item[children_key], _item_key)

    inner(items)
    return index


def collect_request_fields(request, fields, extra_context=None):
    extra_context = extra_context or {}
    request_data = request.GET if request.method == "GET" else request.POST
    data = {}
    for key in fields:
        if key in request_data:
            data[key] = request_data.get(key)
    data.update(extra_context)
    return data


def index_users_by_group(users):
    """
    Create an index of all users by their groups. Some users will appear multiple times
    depending on the groups they are assigned.
    """
    index = {}
    for user in users:
        for group in user.get("groups", []):
            index.setdefault(group, [])
            index[group].append(user)
    for group_name, user_group in index.items():
        user_group.sort(key=lambda user: (user.get("name") or "").upper())
    return index


def validate_required_fields(request, fields):
    errors = {}
    for field in fields:
        if not request.POST.get(field):
            errors[field] = f"{field} is required"
    return errors or None


def compact_list(lst):
    """
    Compact a list removing all non truthful values
    """
    return [item for item in lst if item]


def pluck(dict, attr_list):
    """
    Return a dict containing the attributes listed, plucked from the given dict.
    """
    out = {}
    for key in attr_list:
        if key in dict:
            out[key] = dict[key]
    return out


def is_int(value):
    """
    test if a value (usually string) is a valid int
    """
    try:
        int(float(value))
        return True
    except:
        return False


def submission_contact(submission):
    """
    Extract a contact from a submission.
    A primary contact is preferred, though otherwise the first contact is used.
    """
    contact = submission.get("contact")
    if not contact:
        contacts = (submission.get("organisation") or {}).get("contacts")
        if contacts:
            contacts = (deep_index_items_by(contacts, "primary").get("true") or []) or contacts
            contact = contacts[0] if contacts else None
    if not contact:
        raise Exception("No contact supplied")
    return contact


def public_login_url():
    return f"{settings.PUBLIC_BASE_URL}/"


def notify_footer(api_client, email=None):
    """Build notify footer with specified email.

    :param (Client) api_client: TR API Client.
    :param (str) email: contact email for footer.
    :returns (str): The NOTIFY_BLOCK_FOOTER value provided with email appended
      if any.
    """
    try:
        default_footer = api_client.get_system_parameters("NOTIFY_BLOCK_FOOTER")["value"]
    except APIException as e:
        logger.warning(f"Failed to get NOTIFY_BLOCK_FOOTER system param value: {e}")
        default_footer = "Trade Remedies\nDepartment for International Trade"
    if email:
        return "\n".join([default_footer, f"Contact: {email}"])
    return default_footer


def notify_contact_email(api_client, case_number=None):
    """Build notify email address.

    :param (Client) api_client: TR API Client.
    :param (str) case_number: e.g. 'TD0001'
    :returns (str): If a case is specified returns a case contact email built
      using TRADE_REMEDIES_EMAIL_DOMAIN system parameter, otherwise returns
      TRADE_REMEDIES_EMAIL system parameter.
    """
    if case_number:
        try:
            domain = api_client.get_system_parameters("TRADE_REMEDIES_EMAIL_DOMAIN")["value"]
        except APIException as e:
            logger.warning(f"Failed to get TRADE_REMEDIES_EMAIL_DOMAIN system param value: {e}")
        else:
            return f"{case_number}@{domain}"
    try:
        default_email = api_client.get_system_parameters("TRADE_REMEDIES_EMAIL")["value"]
    except APIException as e:
        logger.warning(f"Failed to get TRADE_REMEDIES_EMAIL system param value: {e}")
        default_email = "investigations@traderemedies.gov.uk"  # /PS-IGNORE
    return default_email


def parse_notify_template(template, values):
    """
    Return a fully parsed notify template text with the given values dict.
    """
    for key, value in values.items():
        value = value or ""
        if key == "footer":
            template = template.replace(f"(({key}))", value.replace("\n", "</br>"))
        elif key == "deadline":
            value = value.replace("<", "&lt;").replace(">", "&gt;")
            template = template.replace(
                f"(({key}))",
                f'<span class="notify-tag" title="{key}" contentEditable=true>{value}</span>',
            )
        else:
            value = value.replace("<", "&lt;").replace(">", "&gt;")
            template = template.replace(
                f"(({key}))", f'<span class="notify-tag" title="{key}">{value}</span>'
            )
    regex = r"([\^])(.+)$"
    matches = re.finditer(regex, template, re.MULTILINE)
    for match in matches:
        groups = match.groups()
        template = "".join(
            [
                template[0 : match.start()],
                '<blockquote style="Margin: 0 0 20px 0; border-left: 10px solid #BFC1C3;padding: 15px 0 0.1px 15px; font-size: 19px; line-height: 25px;">',  # noqa: E501
                groups[1],
                "</blockquote>",
                template[match.end() :],
            ]
        )
    return markdown.markdown(template)


def parse_api_datetime(api_date, result_format=None):
    if not api_date:
        return

    try:
        dt = datetime.strptime(api_date, settings.API_DATETIME_FORMAT)
    except ValueError:
        dt = datetime.strptime(api_date, "%Y-%m-%dT%H:%M:%S.%fZ")

    if result_format:
        return dt.strftime(settings.FRIENDLY_DATE_FORMAT)
    else:
        return dt


def to_json(obj):
    if type(obj) is str:
        return obj
    return json.dumps(obj or {})


def from_json(obj):
    if type(obj) is str:
        return json.loads(obj)
    return obj or {}


def is_date(date_text):
    try:
        parse(date_text)
        return True
    except ValueError:
        return False


def internal_redirect(url, default_path):
    """
    Redirect to the specified URL after checking that
    host is in the allowed hosts list
    :param url: URL to redirect to
    :param default_path: Default path to redirect to if url is unsafe
    """
    if not is_safe_url(url, settings.ALLOWED_HOSTS):
        return redirect(default_path)

    return redirect(url)

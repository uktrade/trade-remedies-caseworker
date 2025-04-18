"""
user_context context processor providing a global user context to
templates which contains the current user's token and basic info
"""

from config.version import __version__
from trade_remedies_client.client import Client
from django.conf import settings


def motd_context(request):
    if settings.DEBUG:
        return {"public_notice": ""}
    return {"public_notice": Client().get_system_parameters("PUBLIC_NOTICE").get("value")}


def user_context(request):
    token = request.session.get("token")
    context = {
        "authenticated": False,
    }
    if token and request.user:
        context["token"] = token
        context["user"] = request.user
        context["user_dict"] = {
            "id": request.user.id,
            "name": request.user.name,
            "email": request.user.email,
        }
        context["authenticated"] = True
    return context


def _get_panel_layout():
    if settings.DEBUG:
        return {"value": False}
    return Client().get_system_parameters("PRE_RELEASE_PANELS", {}).get("value", False)


def page_context(request):
    return {
        "global_header_text": settings.ORGANISATION_NAME,
        "homepage_url": "/cases/",
        "logo_link_title": "Investigator caselist",
        "panel_side": request.COOKIES.get("panel_side"),
        "PANEL_LAYOUT": _get_panel_layout(),
        "SHOW_ENV_BANNER": settings.SHOW_ENV_BANNER,
        "ENV_NAME": settings.ENV_NAME,
        "GIT_BRANCH": settings.GIT_BRANCH,
        "GIT_COMMIT": settings.GIT_COMMIT,
    }


def version_context(request):
    return {"version": {"api": request.session.get("version", ""), "ui": __version__}}


def add_form_errors(request):
    """Pops the form errors from the request.session for front-end rendering.

    This "form_errors" key is then checked in the govuk/base_with_form.html BASE template, and is
    looped over to display the errors in the error summaries box at the top of the page. Individual
    elements can also access this dictionary to retrieve the specific error for that field, e.g. in
    component_macros/text_input.html
    """
    return {"form_errors": request.session.pop("form_errors", None)}


def google_tag_manager(request):
    """Google Tag Manager Id."""
    return {"analytics_manager_id": settings.GOOGLE_ANALYTICS_TAG_MANAGER_ID}

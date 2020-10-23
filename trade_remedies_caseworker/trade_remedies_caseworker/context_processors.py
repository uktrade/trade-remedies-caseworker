"""
user_context context processor providing a global user context to
templates which contains the current user's token and basic info
"""
from trade_remedies_caseworker.version import __version__
from trade_remedies_client.client import Client
from django.conf import settings


def motd_context(request):
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


def page_context(request):
    return {
        "global_header_text": "Trade Remedies Investigations Directorate",
        "homepage_url": "/cases/",
        "logo_link_title": "Investigator caselist",
        "panel_side": request.COOKIES.get("panel_side"),
        "PANEL_LAYOUT": Client()
        .get_system_parameters("PRE_RELEASE_PANELS", {})
        .get("value", False),
        "SHOW_ENV_BANNER": settings.SHOW_ENV_BANNER,
        "ENV_NAME": settings.ENV_NAME,
        "GIT_BRANCH": settings.GIT_BRANCH,
        "GIT_COMMIT": settings.GIT_COMMIT,
    }


def version_context(request):
    return {"version": {"api": request.session.get("version", ""), "ui": __version__}}

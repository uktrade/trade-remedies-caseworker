import sentry_sdk

from core.models import TransientUser
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django_audit_log_middleware import AuditLogMiddleware
from sentry_sdk import set_user


class APIUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        if request.session and request.session.get("token") and request.session.get("user"):
            user = request.session["user"]
            request.user = TransientUser(token=request.session.get("token"), **user)
            request.args = args
            request.kwargs = kwargs
            request.token = request.session["token"]

            # Checking if the user has been logged out by another session, if the session key
            # stored in the cache is different from the one in the current session, then it has
            # been replaced by another login
            """if cache.get(
                request.session["user"]["email"]
            ) != request.session.session_key and not request.path == reverse("logout"):
                request.session["logged_out_by_other_session"] = True
                return redirect(reverse("logout"))"""

            if (
                settings.USE_2FA
                and request.user.should_two_factor
                and request.path not in (reverse("2fa"), reverse("logout"))
            ):
                return redirect("/twofactor/")
        response = self.get_response(request)
        return response


class CacheControlMiddleware:
    """
    Send headers to prevent caching by the browser
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response


class CustomAuditLogMiddleware(AuditLogMiddleware):
    def _get_first_name(self):
        if self.request.user.is_authenticated:
            try:
                return self.request.user.first_name
            except AttributeError:
                pass

        return ""

    def _get_last_name(self):
        if self.request.user.is_authenticated:
            try:
                return self.request.user.last_name
            except AttributeError:
                pass
        return ""


class SentryContextMiddleware:
    """
    Sets sentry context during each request/response so we can identify unique users
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            set_user({"id": request.user.id})
        else:
            set_user(None)
        response = self.get_response(request)
        return response


class TrackForbiddenMiddleware:
    """
    Middleware to track forbidden requests
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 403:
            # Track forbidden requests
            sentry_sdk.capture_message(
                f"URL is forbidden, {request.path}, {response.content}, {request.user.email}"
            )
        return response

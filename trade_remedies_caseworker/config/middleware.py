from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from core.models import TransientUser
from django_audit_log_middleware import AuditLogMiddleware


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

            if (
                    settings.USE_2FA
                    and request.user.should_two_factor
                    and request.path not in (reverse("2fa"), reverse("logout"))
            ):
                return redirect("/twofactor/")
        else:
            print("NO USER!")
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

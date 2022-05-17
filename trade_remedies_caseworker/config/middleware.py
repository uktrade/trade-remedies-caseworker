from core.models import TransientUser
from django.shortcuts import redirect
from django_audit_log_middleware import AuditLogMiddleware

from trade_remedies_caseworker.core.utils import should_2fa


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

            if should_2fa(request):
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

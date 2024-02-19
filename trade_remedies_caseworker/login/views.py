from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from trade_remedies_client.client import Client
from trade_remedies_client.exceptions import APIException
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

from core.decorators import catch_form_errors
from core.utils import internal_redirect


def logout_view(request):
    # logout view

    # we want to pick this up from the session here before it gets deleted
    logged_out_by_other_session = request.session.get("logged_out_by_other_session", False)
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    if logged_out_by_other_session:
        return redirect(f"{reverse('login')}?logged_out_by_other_session=true")
    return redirect("/")


class LoginView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "login.html"

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        password = request.POST.get("password")
        response = self.trusted_client.authenticate(
            email,
            password,
            user_agent=request.META["HTTP_USER_AGENT"],
            ip_address=request.META["REMOTE_ADDR"],
        )
        if response and response.get("token"):
            next_url = request.session.get("next")
            request.session.clear()
            request.session["token"] = response["token"]
            request.session["user"] = response["user"]
            request.session["version"] = response.get("version")
            request.session["errors"] = None
            request.session.cycle_key()
            cache.set(email, request.session.session_key)
            if (
                settings.USE_2FA
                and request.session["user"]["should_two_factor"]
                and request.path not in (reverse("2fa"), reverse("logout"))
            ):
                Client(response["token"]).two_factor_request()
            if next_url:
                return internal_redirect(next_url, "/cases/")
            else:
                return redirect("/cases/")


class TwoFactorView(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    template_name = "two_factor.html"

    def get(self, request, *args, **kwargs):
        twofactor_error = None
        locked_until = None
        resend = request.GET.get("resend")
        delivery_type = request.GET.get("delivery_type")
        if hasattr(request.user, "token") and request.user.should_two_factor:
            if request.session.get("twofactor_error"):
                twofactor_error = request.session["twofactor_error"]
                del request.session["twofactor_error"]
                request.session.modified = True
            if delivery_type != "email" and not request.user.phone:
                delivery_type = "email"
            result = None
            if delivery_type == "email" or resend:
                try:
                    result = self.client(request.user).two_factor_request(
                        delivery_type=delivery_type,
                        user_agent=request.META["HTTP_USER_AGENT"],
                        ip_address=request.META["REMOTE_ADDR"],
                    )
                    if result.get("error"):
                        twofactor_error = result["error"]
                        locked_until = result.get("locked_until")
                except Exception as exc:
                    twofactor_error = (
                        f"We could not send the code "
                        f"to your phone ({request.user.phone}). "
                        f"Please select to use email delivery of the access code."
                    )
                    result = "An error occured"

            return render(
                request,
                self.template_name,
                {
                    "locked_until": locked_until,
                    "two_factor_request": result,
                    "twofactor_error": twofactor_error,
                    "delivery_type": delivery_type,
                },
            )
        else:
            return redirect("/")

    def post(self, request, *args, **kwargs):
        code = request.POST.get("code")
        try:
            result = self.client(request.user).two_factor_auth(
                code=code,
                user_agent=request.META["HTTP_USER_AGENT"],
                ip_address=request.META["REMOTE_ADDR"],
            )
            request.session["user"] = result
            request.session.modified = True
            return redirect("/")
        except APIException as exc:
            if exc.status_code == 401:
                return redirect("/accounts/logout/")
            request.session["twofactor_error"] = (
                "The code you entered is incorrect. Retry or resend code."
            )
            request.session.modified = True
            return redirect("/")

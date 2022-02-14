import os
import json

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from core.constants import (
    SECURITY_GROUP_TRA_ADMINISTRATOR,
    SECURITY_GROUPS_TRA,
    SECURITY_GROUPS_TRA_ADMINS,
    ALERT_MAP,
)
from core.base import GroupRequiredMixin
from core.utils import internal_redirect
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from trade_remedies_client.exceptions import APIException

health_check_token = os.environ.get("HEALTH_CHECK_TOKEN")


def logout_view(request):
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    return redirect("/")


class SystemView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    groups_required = (SECURITY_GROUP_TRA_ADMINISTRATOR,)
    template_name = "system_info.html"

    def get(self, request, *args, **kwargs):
        context = {"body_classes": "full-width"}
        return render(request, self.template_name, context=context)


class HealthCheckView(View, TradeRemediesAPIClientMixin):
    def get(self, request):
        response = self.trusted_client.health_check()
        if all([response[k] == "OK" for k in response]):
            return HttpResponse("OK")
        else:
            return HttpResponse(f"ERROR: {response}")


class LoginView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        email = request.GET.get("email")
        password = request.GET.get("password")
        error = request.GET.get("error")
        request.session["next"] = request.GET.get("next")
        request.session.cycle_key()
        return render(
            request,
            self.template_name,
            {
                "email": email or "",
                "password": password or "",
                "error": request.session.get("errors", None) if error else None,
            },
        )

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
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
                if next_url:
                    return internal_redirect(next_url, "/cases/")
                else:
                    return redirect("/cases/")
            else:
                return redirect("/accounts/login/?error=t")
        except Exception as exc:
            try:
                reason = exc.response.json().get("detail")
            except json.decoder.JSONDecodeError:
                reason = exc.response.text
            except Exception:
                reason = str(exc)
            request.session["errors"] = reason
            return redirect("/accounts/login/?error=1")


class BaseCaseView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = None

    def get(self, request, case_id, submission_id=None, *args, **kwargs):
        pass


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
            request.session[
                "twofactor_error"
            ] = "The code you entered is incorrect. Retry or resend code."
            request.session.modified = True
            return redirect("/")


class ForgotPasswordRequested(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "registration/password_reset_requested.html"


class ForgotPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "registration/reset_password_request.html"

    def post(self, request, *args, **kwargs):
        if email := request.POST.get("email"):
            self.trusted_client.request_password_reset(email)
            return redirect(reverse("forgot_password_requested"))
        return redirect(request.path)


class ResetPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, user_pk, token, *args, **kwargs):
        token_is_valid = self.trusted_client.validate_password_reset(user_pk=user_pk, token=token)
        error_message = kwargs.get("error", None)
        return render(
            request,
            "registration/reset_password.html",
            {
                "token_is_valid": token_is_valid,
                "user_pk": user_pk,
                "token": token,
                "error": error_message,
            },
        )

    def post(self, request, user_pk, token, *args, **kwargs):
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        if password and password_confirm and password == password_confirm:
            try:
                self.trusted_client.reset_password(token, user_pk, password)
                # todo - alert user that their password reset was successful
            except APIException as exc:
                return self.get(request, user_pk, token, error=exc.message)
        elif password != password_confirm:
            return self.get(request, user_pk, token, error="The passwords do not match")
        return redirect_to_login(reverse("cases"), reverse("login"), "next")


class CompaniesHouseSearch(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("term")
        results = self.client(request.user).companies_house_search(query)
        return HttpResponse(json.dumps(results), content_type="application/json")


class SystemParameterSettings(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def get(self, request, *args, **kwargs):
        system_parameters = self.client(request.user).get_system_parameters(editable=True)
        system_parameters.sort(key=(lambda p: p.get("key")))

        return render(
            request,
            "settings/system_parameters.html",
            {
                "body_classes": "full-width",
                "system_parameters": system_parameters,
            },
        )

    def post(self, request, *args, **kwargs):

        regex = r"^original-"
        client = self.client(request.user)
        for sp in client.get_system_parameters(editable=True):
            field = sp.get("key")
            value = request.POST.get(field)
            old_value = request.POST.get("original-" + field)
            old_value = sp.get("value")
            data_type = sp.get("data_type")
            if data_type == "bool":
                value = value == "true"
            if data_type == "int":
                value = int(value or 0)
            if value != old_value:
                if data_type != "list":
                    client.set_system_parameter(field, value)

        return redirect("/settings/system_parameters/")


class FeedbackFormsView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def get(self, request, form_id=None):
        client = self.client(request.user)
        if form_id:
            form = client.get_feedback_form(form_id=form_id)
            collections = client.get_feedback_collections(form_id)
            return render(
                request,
                "feedback/index.html",
                {
                    "body_classes": "full-width",
                    "form": form,
                    "forms": [form],
                    "collections": collections,
                    "mapped_collections": json.dumps({c["id"]: c for c in collections}),
                },
            )

        forms = client.get_feedback_forms()
        return render(
            request,
            "feedback/index.html",
            {"body_classes": "full-width", "forms": forms},
        )


class FeedbackFormExportView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def get(self, request, form_id=None):
        file = self.client(request.user).export_feedback(form_id)
        response = HttpResponse(file, content_type="application/vnd.ms-excel")
        response["Content-Disposition"] = "attachment; filename=trade_remedies_export.xlsx"
        return response

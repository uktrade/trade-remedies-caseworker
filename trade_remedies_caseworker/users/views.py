import pytz
import json
from django.views.generic import TemplateView
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from trade_remedies_client.exceptions import APIException
from core.utils import validate_required_fields, pluck, get
from core.constants import SECURITY_GROUP_SUPER_USER


class UserBaseTemplateView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    pass


class UserManagerView(UserBaseTemplateView):
    template_name = "settings/users.html"

    def get(self, request, user_group=None, *args, **kwargs):
        tab = request.GET.get("tab", "caseworker")
        tabs = {
            "value": tab,
            "tabList": [
                {"label": "Investigators", "value": "caseworker"},
                {"label": "Customers", "value": "public"},
                {"label": "Incomplete customer accounts", "value": "pending"},
            ],
        }
        user_group = {
            "caseworker": "caseworker",
            "public": "public",
            "pending": "public",
        }[tab]
        client = self.client(request.user)
        users = client.get_all_users(group_name=user_group)
        users.sort(key=lambda user: user.get("created_at"), reverse=True)

        return render(
            request,
            self.template_name,
            {
                "user_group": user_group,
                "users": users,
                "inactive_user_count": sum(user["active"] is False for user in users),
                "body_classes": "full-width",
                "tabs": tabs,
            },
        )


class UserView(UserBaseTemplateView):

    delete_user = False
    template_name = "settings/user.html"

    user_fields = json.dumps(
        {
            "Case": {
                "id": 0,
                "name": 0,
                "reference": 0,
                "workflow_state": {"MEASURE_EXPIRY": 0, "LATEST_MEASURE_EXPIRY": 0},
            }
        }
    )

    def get(self, request, user_id=None, user_group=None, *args, **kwargs):
        user = kwargs.get("user", {})
        client = self.client(request.user)
        job_titles = client.get_all_job_titles()
        case_enums = client.get_all_case_enums()
        groups = client.get_security_groups(user_group)
        cases = []
        if user_id:
            cases = client.get_user_cases(
                archived="all",
                request_for=user_id,
                all_cases=False,
                fields=self.user_fields,
            )
        str_now = timezone.now().strftime(settings.API_DATETIME_FORMAT)
        for case in cases:
            expiry = get(case, "workflow_state/LATEST_MEASURE_EXPIRY/0") or get(
                case, "workflow_state/MEASURE_EXPIRY/0"
            )
            if expiry and expiry < str_now:
                cases.remove(case)
        if user_id and not user:
            user = client.get_user(user_id)
        else:
            user["country_code"] = user.get("country_code", "GB")
            user["timezone"] = user.get("timezone", "Europe/London")
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "job_titles": job_titles,
                "user_group": user_group,
                "edit_user": user,
                "timezones": pytz.common_timezones,
                "groups": groups,
                "errors": kwargs.get("errors", []),
                "super_user_role": SECURITY_GROUP_SUPER_USER,
                "countries": case_enums.get("countries", []),
                "cases": cases,
            },
        )

    def post(self, request, user_id=None, user_group=None, *args, **kwargs):
        client = self.client(request.user)

        if self.delete_user:
            result = client.delete_user(user_id=user_id)
            return HttpResponse(json.dumps({"alert": "User deleted.", "redirect_url": "reload"}))

        required_fields = ["name", "email", "roles"]
        if not user_id:
            required_fields += ["password", "password_confirm"]

        user = {}
        if user_id:
            user = client.get_user(user_id)
        else:
            user["email"] = request.POST.get("email")  # Can't update email
        user.update(
            pluck(
                request.POST,
                [
                    "name",
                    "phone",
                    "timezone",
                    "roles",
                    "job_title_id",
                    "active",
                    "set_verified",
                ],
            )
        )
        user["country"] = request.POST.get("country", user.get("country_code"))
        user["groups"] = request.POST.getlist(
            "roles"
        )  # translation needed as the create write key doesn't match the update
        if not user_id:
            user["country_code"] = request.POST.get(
                "country"
            )  # bodge as create doesn't match update

        errors = validate_required_fields(request, required_fields) or {}
        password = request.POST.get("password")
        if password:
            user["password"] = password
            user["password_confirm"] = request.POST.get("password_confirm")
            if password != request.POST.get("password_confirm"):
                errors["password_confirm"] = "Confirmation password does not match"

        if not errors:
            try:
                response = client.create_or_update_user(user, user_id=user_id)
            except APIException as exc:
                errors = exc.detail.get("errors", [])
                return self.get(
                    request,
                    user_id=user_id,
                    user_group=user_group,
                    errors=errors,
                    user=user,
                )
            else:
                return HttpResponse(json.dumps({"result": response}))
        else:
            return self.get(
                request,
                user_id=user_id,
                user_group=user_group,
                errors=errors,
                user=user,
                *args,
                **kwargs,
            )


class MyAccountView(UserBaseTemplateView):
    template_name = "settings/my_account.html"

    def get(self, request, *args, **kwargs):
        client = self.client(request.user)
        job_titles = client.get_all_job_titles()
        case_enums = client.get_all_case_enums()
        user = kwargs.get("user", client.get_my_account())
        user = client.get_my_account()
        user.setdefault("country_code", "GB")
        user.setdefault("timezone", "Europe/London")
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "job_titles": job_titles,
                "edit_user": user,
                "timezones": pytz.common_timezones,
                "errors": kwargs.get("errors", []),
                "countries": case_enums.get("countries", []),
                "safe_colours": case_enums.get("safe_colours"),
            },
        )

    def post(self, request, *args, **kwargs):
        required_fields = ["name", "email"]
        client = self.client(request.user)
        user = client.get_my_account()
        user["name"] = request.POST.get("name")
        user["country"] = request.POST.get("country", user.get("country_code"))
        user["phone"] = request.POST.get("phone", user.get("phone"))
        user["timezone"] = request.POST.get("timezone", user.get("timezone"))
        user["job_title_id"] = request.POST.get("job_title_id") or None
        user["colour"] = request.POST.get("colour") or user.get("colour")

        errors = validate_required_fields(request, required_fields) or {}
        password = request.POST.get("password")
        do_logout = False
        if password:
            user["password"] = password
            user["password_confirm"] = request.POST.get("password_confirm")
            if password != request.POST.get("password_confirm"):
                errors["password_confirm"] = "Confirmation password does not match"
            else:
                do_logout = True
        if not errors:
            try:
                response = client.update_my_account(user)
            except APIException as exc:
                errors = exc.detail.get("errors", [])
                return self.get(request, errors=errors, user=user)
            else:
                request.session["user"] = response
                response["redirect_url"] = "/accounts/logout/"
                response["alert"] = (
                    "You have changed your password and will be logged out. "
                    "Please log in using your updated password."
                )
                response["pop_alert"] = True
                return HttpResponse(json.dumps(response))
        else:
            return self.get(request, errors=errors, user=user, *args, **kwargs)


class ContactLookupView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, *args, **kwargs):
        search = request.GET.get("email")
        contact_id = request.GET.get("contact_id")
        client = self.client(request.user)
        return HttpResponse(
            json.dumps(
                {
                    "result": client.lookup_contacts(search)
                    if search
                    else client.get_contact(contact_id)
                }
            ),
            content_type="application/json",
        )

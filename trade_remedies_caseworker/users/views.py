import logging
import pytz
import json
from requests.exceptions import HTTPError
from django.views.generic import TemplateView
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from trade_remedies_client.exceptions import APIException
from core.base import GroupRequiredMixin
from core.utils import validate_required_fields, pluck, get
from core.constants import SECURITY_GROUP_TRA_ADMINISTRATOR, SECURITY_GROUPS_TRA_ADMINS


logger = logging.getLogger(__name__)


class UserBaseTemplateView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    pass


class UserManagerView(UserBaseTemplateView, GroupRequiredMixin):

    groups_required = SECURITY_GROUPS_TRA_ADMINS
    template_name = "settings/users.html"

    def get(self, request, *args, **kwargs):
        tab = request.GET.get("tab", "caseworker")
        tabs = {
            "value": tab,
            "tabList": [
                {"label": "Investigators", "value": "caseworker"},
                {"label": "Customers", "value": "public"},
                {"label": "Incomplete customer accounts", "value": "pending"},
            ],
        }
        create_url = {
            "caseworker": {"url": reverse("create_investigator"), "label": "Investigator"},
            "public": {"url": reverse("create_customer"), "label": "Customer"},
            "pending": {"url": reverse("create_customer"), "label": "Customer"},
        }[tab]
        client = self.client(request.user)
        group_name = "caseworker" if tab == "caseworker" else "public"
        users = client.get_all_users(group_name=group_name)
        users.sort(key=lambda usr: usr.get("created_at"), reverse=True)
        for user in users:
            user_id = user["id"]
            url = {
                "caseworker": reverse("edit_investigator", args=(user_id,)),
                "public": reverse("edit_customer", args=(user_id,)),
                "pending": reverse("edit_customer", args=(user_id,)),
            }[tab]
            user["url"] = url
        return render(
            request,
            self.template_name,
            {
                "create_url": create_url,
                "users": users,
                "inactive_user_count": sum(user["active"] is False for user in users),
                "body_classes": "full-width",
                "tabs": tabs,
                "tra_admin_role": SECURITY_GROUP_TRA_ADMINISTRATOR,
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

    def get(self, request, user_id=None, *args, **kwargs):
        user = kwargs.get("user", {})
        client = self.client(request.user)
        job_titles = client.get_all_job_titles()
        case_enums = client.get_all_case_enums()
        group_name = "customer"
        if request.resolver_match.url_name.endswith("investigator"):
            group_name = "caseworker"
        editing_customer = group_name == "customer"
        groups = client.get_security_groups(group_name)
        cases = []
        is_admin = SECURITY_GROUP_TRA_ADMINISTRATOR in request.user.groups
        can_edit = any(
            [
                is_admin,
                str(user_id) == request.user.id,
                editing_customer,
            ]
        )
        challenge_password = all(
            [
                not is_admin,
                not editing_customer,
            ]
        )
        form_actions = {
            "create_investigator": reverse("create_investigator"),
            "create_customer": reverse("create_customer"),
        }
        if user_id:
            form_actions.update(
                {
                    "edit_investigator": reverse("edit_investigator", args=(user_id,)),
                    "edit_customer": reverse("edit_customer", args=(user_id,)),
                }
            )
            cases = client.get_user_cases(
                archived="all",
                request_for=user_id,
                all_cases=False,
                fields=self.user_fields,
            )
        else:
            # Create user attempt
            if SECURITY_GROUP_TRA_ADMINISTRATOR not in request.user.groups:
                logger.warning(f"Attempt by {request.user.email} to create user")
                return HttpResponseForbidden()
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
        form_action = form_actions[request.resolver_match.url_name]
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "job_titles": job_titles,
                "form_action": form_action,
                "editing_customer": editing_customer,
                "challenge_password": challenge_password,
                "read_only": not can_edit,
                "tra_admin_role": SECURITY_GROUP_TRA_ADMINISTRATOR,
                "edit_user": user,
                "timezones": pytz.common_timezones,
                "groups": groups,
                "errors": kwargs.get("errors", []),
                "countries": case_enums.get("countries", []),
                "cases": cases,
            },
        )

    def post(self, request, user_id=None, user_group=None, *args, **kwargs):
        client = self.client(request.user)

        if self.delete_user:
            result = client.delete_user(user_id=user_id)
            return HttpResponse(json.dumps({"alert": "User deleted.", "redirect_url": "reload"}))

        required_fields = ["name", "email"]
        if SECURITY_GROUP_TRA_ADMINISTRATOR in request.user.groups:
            required_fields.append("roles")
        user = {}
        if user_id:
            user = client.get_user(user_id)
        else:
            user["email"] = request.POST.get("email")  # Can't update email
            required_fields += ["password", "password_confirm"]
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
        if password_errors := self.validate_password(request, user):
            errors.update(password_errors)
        else:
            if pwd := request.POST.get("password"):
                user["password"] = pwd
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

    def validate_password(self, request, user=None):
        """Validate password.

        Checks if this is a user create or update and validates
        password fields accordingly.

        :param (HTTPRequest) request: in flight request.
        :param (dict) user: user being updated.
        :returns (dict): errors dict.
        """
        errors = {}
        if not user:
            user = {}
        create_mode = False
        if request.resolver_match.url_name.startswith('create_'):
            create_mode = True
        is_admin = SECURITY_GROUP_TRA_ADMINISTRATOR in request.user.groups
        password_update_attempt = any(
            [
                current_password := request.POST.get("current_password"),
                password := request.POST.get("password"),
                password_confirm := request.POST.get("password_confirm"),
                create_mode,
            ]
        )
        if not password_update_attempt:
            return errors

        if password != password_confirm:
            errors["password_confirm"] = "Confirmation password does not match"

        skip_challenge = any(
            [
                create_mode,
                is_admin,
                not user["tra"],  # we're editing a customer
            ]
        )
        if skip_challenge:
            return errors

        try:
            response = self.trusted_client.authenticate(
                    user.get("email"),
                    current_password,
                    user_agent=request.META["HTTP_USER_AGENT"],
                    ip_address=request.META["REMOTE_ADDR"],
            )
        except HTTPError:
            errors["current_password"] = "Invalid current password"
        except APIException:
            errors["current_password"] = "Failed to validate current password"
        else:
            if not response.get("token"):
                errors["current_password"] = "Invalid current password"
        return errors


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

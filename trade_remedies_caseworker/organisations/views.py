import datetime
import json
import logging
import urllib.parse
from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render, redirect
from django.utils.http import urlencode
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django_countries import countries
from core.base import FeatureFlagMixin
from core.constants import (
    CASE_ROLE_AWAITING_APPROVAL,
    CASE_ROLE_REJECTED,
    CASE_ROLE_APPLICANT,
    CASE_ROLE_PREPARING,
)
from core.utils import (
    collect_request_fields,
    parse_notify_template,
    public_login_url,
    deep_index_items_by_exists,
    deep_index_items_by,
    get,
)
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from trade_remedies_client.exceptions import APIException

contact_fields = [
    "contact_name",
    "contact_email",
    "contact_phone",
    "contact_address",
    "contact_post_code",
    "contact_country",
    "primary_contact",
]

org_fields = [
    "organisation_name",
    "companies_house_id",
    "organisation_address",
    "organisation_post_code",
    "organisation_type",
    "vat_number",
    "eori_number",
    "duns_number",
    "organisation_website",
    "organisation_country",
    "organisation_id",
    "json_data",
]

logger = logging.getLogger(__name__)


def invite_template_change(request):
    if request.method != "POST":
        logger.error(f"invite_template_change expected POST but received {request.method}")
        return HttpResponseBadRequest()

    case_id = request.POST.get("data_dict[case_id]")
    try:
        case_request_fields = {
            "initiated_at": datetime.datetime.strptime(
                request.POST.get("data_dict[deadline]"), "%d %b %Y"
            ).replace(tzinfo=datetime.timezone.utc),
        }
    except ValueError:
        case_request_fields = {
            "initiated_at": datetime.datetime.strptime(
                request.POST.get("data_dict[deadline]"), "%d %B %Y"
            ).replace(tzinfo=datetime.timezone.utc),
        }
    if request.user.is_authenticated:
        _client = TradeRemediesAPIClientMixin.client(request, request.user)
        _client.update_case(case_id, case_request_fields)
        return HttpResponse(json.dumps({"updated": True}))

    return HttpResponse(json.dumps({"updated": False}))


class BaseOrganisationTemplateView(
    LoginRequiredMixin, FeatureFlagMixin, TemplateView, TradeRemediesAPIClientMixin
):
    def dispatch(self, *args, **kwargs):
        self._client = None
        if self.request.user.is_authenticated:
            self._client = self.client(self.request.user)
        return super().dispatch(*args, **kwargs)

    def return_redirect(self, alert=None):
        coded_alert = urlencode({"alert": alert})
        return HttpResponse(
            json.dumps({"redirect_url": f"?{coded_alert}"}),
            content_type="application/json",
        )


class OrganisationsView(BaseOrganisationTemplateView):
    template_name = "organisations/organisations.html"
    fields = json.dumps(
        {
            "Organisation": {
                "id": 0,
                "name": 0,
                "country": {
                    "code": 0,
                    "name": 0,
                },
                "created_at": 0,
                "companies_house_id": 0,
                "fraudulent": 0,
                "case_count": 0,
                "user_count": 0,
            }
        }
    )

    def get(self, request, *args, **kwargs):
        organisations = self._client.get_organisations(fields=self.fields)
        organisations.sort(key=lambda org: get(org, "name", "").lower())
        groups = {"active": [], "inactive": [], "fraudulent": []}
        for organisation in organisations:
            if organisation.get("fraudulent"):
                groups["fraudulent"].append(organisation)
            elif not organisation.get("case_count"):
                groups["inactive"].append(organisation)
            else:
                groups["active"].append(organisation)

        tab = request.GET.get("tab") or "active"
        tabs = {
            "value": tab,
            "tabList": [
                {
                    "label": "Active organisations",
                    "value": "active",
                    "sr_text": "Organisations that have case participations",
                },
                {
                    "label": "Fraudulent",
                    "value": "fraudulent",
                    "sr_text": "Organisations that have been marrked as fraudulent",
                },
                {
                    "label": "No case participation",
                    "value": "inactive",
                    "sr_text": "Organisations tha have never participated in a case",
                },
            ],
        }
        for tab_iter in tabs.get("tabList"):
            tab_iter["count"] = len(groups.get(tab_iter["value"]) or [])

        return render(
            request,
            self.template_name,
            {
                "tabs": tabs,
                "body_classes": "full-width",
                "organisations": groups.get(tab),
            },
        )


class OrganisationView(BaseOrganisationTemplateView):
    template_name = "organisations/organisation.html"

    def get(self, request, organisation_id, *args, **kwargs):
        organisation = self._client.get_organisation(organisation_id)
        cases = self._client.organisation_cases(organisation_id)
        users = self._client.get_organisation_users(organisation_id)
        cases_idx = deep_index_items_by_exists(cases, "archived_at")
        organisation.update({"users": users})
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "organisation": organisation,
                "party": organisation,
                "cases_idx": cases_idx,
            },
        )


class OrganisationNameChangeView(BaseOrganisationTemplateView):
    template_name = "organisations/organisation_name.html"

    def get(self, request, organisation_id, *args, **kwargs):
        organisation = self._client.get_organisation(organisation_id)
        disable_country_selection = organisation.get("country", {}).get("code") == "GB"
        return render(
            request,
            self.template_name,
            {
                "body_classes": "full-width",
                "organisation": organisation,
                "party": organisation,
                "countries": countries,
                "disable_country_selection": disable_country_selection,
            },
        )

    def post(self, request, organisation_id, *args, **kwargs):
        organisation = self._client.get_organisation(organisation_id)
        org_request_fields = collect_request_fields(request, org_fields)
        if org_request_fields.get("organisation_name") != organisation.get("name"):
            response = self._client.update_organisation(organisation_id, org_request_fields)
        return redirect(f"/organisations/{organisation_id}/")


class OrganisationFormView(BaseOrganisationTemplateView):
    template_name = "organisations/organisation_form.html"
    raise_exception = True

    def get(
        self,
        request,
        case_id=None,
        organisation_id=None,
        organisation_type=None,
        *args,
        **kwargs,
    ):
        role = {}
        all_roles = self._client.get_case_roles()
        if organisation_id and case_id:
            organisation = self._client.get_organisation(organisation_id, case_id=case_id)
            role = organisation.get("case_role", {})
        elif organisation_id:
            organisation = self._client.get_organisation(organisation_id)
        else:
            organisation = {
                "new": True,
                "id": "",
                "organisation": {"id": ""},
                "contact": {},
            }
        if organisation_type and not role:
            role = self._client.get_case_role(organisation_type)
        elif role:
            organisation_type = role.get("key")
        context = {
            "case_id": case_id,
            "organisation": organisation,
            "organisation_type": organisation_type,
            "organisation_type_spec": role,
            "countries": countries,
            "case_roles": all_roles,
            "show_contact_form": organisation.get("new"),
        }
        return render(request, self.template_name, context)

    def post(
        self,
        request,
        case_id=None,
        organisation_id=None,
        organisation_type=None,
        *args,
        **kwargs,
    ):
        extra_context = {"case_id": str(case_id)}
        org_request_fields = collect_request_fields(request, org_fields, extra_context)
        if organisation_id:
            organisation = self._client.update_organisation(organisation_id, org_request_fields)
        else:
            # create new org and add to case
            organisation = get(
                self._client.update_case_organisation_by_type(
                    case_id, organisation_type, org_request_fields
                ),
                "organisation",
            )
            if not org_request_fields.get("organisation_id") and organisation:
                contact_request_fields = collect_request_fields(
                    request, contact_fields, extra_context
                )
                contact_request_fields["organisation_id"] = organisation["id"]
                if contact_request_fields.get("contact_name") and contact_request_fields.get(
                    "contact_email"
                ):
                    contact = self._client.create_contact(contact_request_fields)
            return self.return_redirect("Created party " + organisation.get("name"))
        return HttpResponse(json.dumps({"organisation": organisation}))


class ContactFormView(BaseOrganisationTemplateView):
    template_name = "organisations/contact_form.html"
    raise_exception = True

    def get(
        self,
        request,
        case_id=None,
        organisation_id=None,
        contact_id=None,
        *args,
        **kwargs,
    ):
        organisation = self._client.get_organisation(organisation_id)
        if contact_id:
            contact = self._client.get_contact(contact_id)
        else:
            contact = {}
        context = {
            "case_id": case_id,
            "organisation": organisation,
            "contact": contact,
            "is_email_read_only": self.feature_flags("contact_email_read_only"),
            "countries": countries,
            "errors": kwargs.get("errors"),
        }
        return render(request, self.template_name, context)

    def post(
        self,
        request,
        case_id=None,
        organisation_id=None,
        contact_id=None,
        *args,
        **kwargs,
    ):
        request_fields = [
            "contact_name",
            "contact_phone",
            "contact_address",
            "contact_post_code",
            "contact_country",
            "primary_contact",
            "contact_id",
        ]

        if not self.feature_flags("contact_email_read_only"):
            request_fields.append("contact_email")

        request_fields = collect_request_fields(request, request_fields)
        contact_name = request_fields.get("contact_name")
        errors = None
        try:
            if contact_id:
                response = self._client.update_contact(contact_id, request_fields)
            else:
                response = self._client.create_and_add_contact(
                    case_id, organisation_id, request_fields
                )
        except APIException as exc:
            errors = exc.detail.get("errors")
        if errors:
            return self.get(
                request,
                case_id=case_id,
                organisation_id=organisation_id,
                contact_id=contact_id,
                errors=errors,
            )
        return HttpResponse(json.dumps({"updated": True}))


class ContactDeleteView(BaseOrganisationTemplateView):
    def post(self, request, contact_id, case_id=None, organisation_id=None, *args, **kwargs):
        response = self._client.delete_contact(contact_id)
        return HttpResponse(json.dumps(response))


class ContactPrimaryView(BaseOrganisationTemplateView):
    def post(
        self,
        request,
        organisation_id=None,
        contact_id=None,
        case_id=None,
        *args,
        **kwargs,
    ):
        response = self._client.set_case_primary_contact(contact_id, organisation_id, case_id)
        name = response.get("name", "")
        return HttpResponse(json.dumps(response))
        return self.return_redirect(f'Primary contact set to "{name}"')


class ToggleUserAdmin(BaseOrganisationTemplateView):
    def post(self, request, organisation_id=None, user_id=None, *args, **kwargs):
        response = self._client.toggle_user_admin(user_id, organisation_id)
        name = response.get("name", "")
        return self.return_redirect(f'User "{name}" set to admin')


class ToggleOrganisationSampledView(BaseOrganisationTemplateView):
    def post(self, request, organisation_id, case_id, *args, **kwargs):
        response = self._client.toggle_organisation_sampled(organisation_id, case_id)
        org_name = (response.get("organisation") or {}).get("name")
        sampled_str = "added to sample" if response.get("sampled") else "removed from sample"
        return self.return_redirect(f'Party "{org_name}" {sampled_str}')


class ToggleOrganisationNonResponsiveView(BaseOrganisationTemplateView):
    def post(self, request, organisation_id, case_id, *args, **kwargs):
        redirect_path = request.GET.get("redirect", f"/case/{case_id}/parties/")
        response = self._client.toggle_organisation_nonresponsive(organisation_id, case_id)
        org_name = (response.get("organisation") or {}).get("name")
        responsive_str = (
            "marked as non-cooperative"
            if response.get("non_responsive")
            else "marked as cooperative"
        )
        return self.return_redirect(f'Party "{org_name}" {responsive_str}')


class OrganisationCaseRoleView(BaseOrganisationTemplateView):
    template_name = "organisations/organisation_approval.html"

    def get(self, request, case_id, organisation_id, *args, **kwargs):
        action = request.GET.get("action")
        organisation = self._client.get_organisation(organisation_id, case_id)
        case = self._client.get_case(case_id)
        roles = self._client.get_case_roles(
            exclude=[
                CASE_ROLE_APPLICANT,
                CASE_ROLE_AWAITING_APPROVAL,
                CASE_ROLE_REJECTED,
                CASE_ROLE_PREPARING,
            ]
        )
        contacts = organisation["contacts"]
        notify_key = (
            "NOTIFY_COMPANY_ROLE_CHANGED"
            if action in ("approve", "change")
            else "NOTIFY_COMPANY_ROLE_DENIED"
        )
        notification_template = self._client.get_notification_template(notify_key)
        values = {
            "case_name": case["name"],
            "case_number": case["reference"],
            "notice": "",
            "company_name": organisation["name"],
            "login_url": public_login_url(),
            "previous_role": organisation.get("case_role", {}).get("name"),
        }
        values = self._client.create_notify_context(values)
        context = {
            "case": case,
            "data_substitute": "new_role",
            "editable_fields": {  # Leaving one for future reference
                # 'case': {'title': 'Case Name'},
            },
            "values": values,
            "organisation": organisation,
            "contacts": contacts,
            "contact_id": contacts[0]["id"] if len(contacts) == 1 else None,
            "action": action,
            "roles": roles,
            "parsed_template": parse_notify_template(notification_template["body"], values),
            "notification_template": notification_template,
            "organisation_type": request.GET.get("organisation_type")
            or CASE_ROLE_AWAITING_APPROVAL,
        }
        return render(request, self.template_name, context)

    def post(self, request, case_id, organisation_id, *args, **kwargs):
        action = request.POST.get("action", "change")
        role_key = request.POST.get("organisation_type") or request.POST.get("role_key")
        contact_id = request.POST.get("contact_id")
        next_url = request.POST.get("next", f"/case/{case_id}/admin/")
        response = self._client.approval_notify(
            case_id=case_id,
            organisation_id=organisation_id,
            action=action,
            values={"organisation_type": role_key, "contact_id": contact_id},
        )
        return HttpResponse(json.dumps({"redirect_url": next_url}))


class OrganisationDedupeView(BaseOrganisationTemplateView):
    template_name = "organisations/dedupe.html"

    def get(self, request, *args, **kwargs):
        left_name = request.GET.get("left")
        right_name = request.GET.get("right", left_name)
        limit = request.GET.get("limit")
        duplicate_orgs = self._client.get_duplicate_organisations(limit=limit)
        context = {
            "limit": limit or 50,
            "duplicates": duplicate_orgs["duplicates"],
            "similar": duplicate_orgs["similar"],
            "left": left_name,
            "right": right_name,
            "names": [left_name, right_name],
        }
        # if names provided grab both orgs and their cases
        if left_name and right_name:
            organisations = self._client.get_organisation_id_by_name(
                names=list(set(context["names"])), case_summary=True
            )
            context["organisations"] = organisations
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        If confirm is true, merge the right name into the left one.
        """
        left_name = request.POST.get("left")
        right_name = request.POST.get("right")
        confirm = request.POST.get("confirm")


class OrganisationDeleteView(BaseOrganisationTemplateView):
    def post(self, request, organisation_id, case_id=None, *args, **kwargs):
        """
        Delete this party provided it has no users
        """
        result = self._client.delete_organisation(organisation_id)
        party_name = result.get("name", "unknown")
        alert = urllib.parse.quote(f'Party "{party_name}" deleted')
        if case_id:
            return redirect(f"/case/{case_id}/parties?alert={alert}")
        return redirect(f"/cases/?alert={alert}")


class OrganisationRemoveView(BaseOrganisationTemplateView):
    def post(self, request, organisation_id, case_id, *args, **kwargs):
        """
        Remove this party from the case by deleting  the caserole
        """
        result = self._client.remove_organisation_from_case(
            case_id=case_id, organisation_id=organisation_id
        )
        party_name = result.get("name", "unknown")
        alert = urllib.parse.quote(f'Party "{party_name}" removed from case')
        if case_id:
            return redirect(f"/case/{case_id}/parties?alert={alert}")
        return redirect(f"/cases/?alert={alert}")


class OrganisationMergeView(BaseOrganisationTemplateView):
    def post(self, request, organisation_id, *args, **kwargs):

        merge_with = request.POST.getlist("merge_with")
        parameter_map = request.POST.get("parameter_map")
        result = self.client(self.request.user).organisation_merge(
            organisation_id=organisation_id, merge_with=merge_with, params=parameter_map
        )
        return HttpResponse(json.dumps({"result": result}), content_type="application/json")


class OrganisationDuplicatesView(LoginRequiredMixin, View, TradeRemediesAPIClientMixin):
    def get(self, request, organisation_id, *args, **kwargs):
        org_matches = self.client(self.request.user).get_organisation_matches(
            organisation_id, with_details="none"
        )
        org_index = deep_index_items_by(org_matches, "id")
        for match in org_matches:
            match_id = get(match, "id")
            no_merge = get(match, "json_data/no_merge") or {}
            if str(match_id) == str(organisation_id):
                # this is our org, so remove everything from the no-merge list
                for nm_id, details in no_merge.items():
                    if str(nm_id) in org_index:
                        del org_index[str(nm_id)]
            else:
                # This is not our org, so remove it if our org id is in its no-merge list
                for nm_id, details in no_merge.items():
                    if str(nm_id) == str(organisation_id) and str(match_id) in org_index:
                        del org_index[str(match_id)]

        return HttpResponse(
            json.dumps(
                {
                    "org_matches": [org_array[0] for org_array in org_index.values()],
                }
            ),
            content_type="application/json",
        )


class OrganisationMatchView(BaseOrganisationTemplateView):
    template_name = "cases/organisation_selection.html"

    def get(self, request, *args, **kwargs):
        organisation_name = request.GET.get("organisation_name")
        companies_house_id = request.GET.get("companies_house_id")
        matching_orgs = self._client.get_organisation_matches(
            name=organisation_name, companies_house_id=companies_house_id
        )
        return render(
            request,
            self.template_name,
            {
                "case": None,
                "organisation": None,
                "org_matches": matching_orgs,
            },
        )
        # return HttpResponse(json.dumps({
        #    'result': duplicate_orgs
        # }), content_type='application/json')

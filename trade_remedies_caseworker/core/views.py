import os
import json

from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from core.constants import (
    SECURITY_GROUP_TRA_ADMINISTRATOR,
    SECURITY_GROUPS_TRA,
    SECURITY_GROUPS_TRA_ADMINS,
)
from core.base import GroupRequiredMixin
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from v2_api_client.mixins import APIClientMixin

health_check_token = os.environ.get("HEALTH_CHECK_TOKEN")


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


class BaseCaseView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    groups_required = SECURITY_GROUPS_TRA
    template_name = None

    def get(self, request, case_id, submission_id=None, *args, **kwargs):
        pass


class CompaniesHouseSearch(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("term")
        results = self.client(request.user).companies_house_search(query)
        return HttpResponse(json.dumps(results), content_type="application/json")


class OrganisationNameSearch(TemplateView, LoginRequiredMixin, APIClientMixin):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("term")
        results = self.client.organisations.get_organisations_by_company_name(query)
        organisations = {"organisations": [each.data_dict for each in results]}
        return HttpResponse(json.dumps(organisations), content_type="application/json")


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


class ViewFeatureFlags(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = SECURITY_GROUPS_TRA_ADMINS
    template_name = "v2/feature_flags/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_flags"] = self.client(self.request.user).v2_get_all_feature_flags()
        return context


class ViewOneFeatureFlag(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = SECURITY_GROUPS_TRA_ADMINS
    template_name = "v2/feature_flags/retrieve.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_flag"] = self.client(self.request.user).v2_get_one_feature_flag(
            kwargs["feature_flag_name"]
        )
        return context


class EditUserGroup(LoginRequiredMixin, GroupRequiredMixin, View, APIClientMixin):
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def post(self, request, group_name):
        getattr(self.client, request.GET["method"])(
            self.client.url(f"users/{request.POST['user_to_change']}/change_group"),
            data={"group_name": group_name},
        )
        return redirect(reverse("view_feature_one_flag", kwargs={"feature_flag_name": group_name}))

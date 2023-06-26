from django.shortcuts import redirect
from django.urls import reverse

from config.base_views import BaseCaseWorkerView, FormInvalidMixin
from core.constants import SECURITY_GROUPS_TRA_ADMINS
from organisations.v2.forms import AdhocMergeForm


class StartView(FormInvalidMixin, BaseCaseWorkerView):
    template_name = "v2/adhoc_organisation_merge/start.html"
    form_class = AdhocMergeForm
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def form_valid(self, form):
        omr = self.client.organisation_merge_records.adhoc_merge(
            organisation_1_id=form.cleaned_data["organisation_1"],
            organisation_2_id=form.cleaned_data["organisation_2"],
        )
        self.request.session["came_from_adhoc_merge"] = True

        duplicate_organisation_merge_id = omr.potential_duplicates[0]["id"]
        return redirect(
            reverse(
                "organisations:merge_organisations_select_differences",
                kwargs={
                    "organisation_merge_record_id": omr["id"],
                    "duplicate_organisation_merge_id": duplicate_organisation_merge_id,
                },
            )
        )

    def form_invalid(self, form):
        return super().form_invalid(form)

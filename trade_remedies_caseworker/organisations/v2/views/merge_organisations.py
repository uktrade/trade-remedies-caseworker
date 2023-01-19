from django.shortcuts import redirect
from django.urls import reverse

from config.base_views import BaseCaseWorkerView, FormInvalidMixin
from organisations.v2.forms import MergeOrganisationsSelectDifferencesForm, ReviewMergeForm


class SelectDifferencesView(BaseCaseWorkerView, FormInvalidMixin):
    template_name = "v2/merge_organisations/select_differences.html"
    form_class = MergeOrganisationsSelectDifferencesForm

    def dispatch(self, request, *args, **kwargs):
        self.duplicate_organisation_merge = self.client.duplicate_organisation_merges(
            self.kwargs["duplicate_organisation_merge_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parent_organisation"] = self.duplicate_organisation_merge.parent_organisation
        context["child_organisation"] = self.duplicate_organisation_merge.child_organisation
        context["duplicate_organisation_merge"] = self.duplicate_organisation_merge
        return context

    def form_valid(self, form):
        organisation_lookup = {
            self.duplicate_organisation_merge.parent_organisation.id: [],
            self.duplicate_organisation_merge.child_organisation.id: [],
        }
        for key, value in form.cleaned_data.items():
            if value:
                if key == "address":
                    # if the address is selected, we need to also copy over the post_code and
                    # country as these are stored in separate fields but are displayed together.
                    organisation_lookup[value].append("post_code")
                    organisation_lookup[value].append("country")
                organisation_lookup[value].append(key)

        # now we have a list of the differences, we can save them to the merge object so they can
        # be actioned upon and merged later.
        self.duplicate_organisation_merge.update(
            {
                "parent_fields": organisation_lookup[
                    self.duplicate_organisation_merge.parent_organisation.id
                ],
                "child_fields": organisation_lookup[
                    self.duplicate_organisation_merge.child_organisation.id
                ],
                "status": 4,
            }
        )

        # todo - return to the merge page for remaining duplicate potential merges
        return redirect(
            reverse(
                "organisations:merge_organisations_review",
                kwargs={
                    "organisation_merge_record_id": self.duplicate_organisation_merge.merge_record
                },
            )
        )


class ReviewMergeView(BaseCaseWorkerView, FormInvalidMixin):
    template_name = "v2/merge_organisations/review_merge.html"
    form_class = ReviewMergeForm

    def dispatch(self, request, *args, **kwargs):
        self.organisation_merge_record = self.client.organisation_merge_records(
            self.kwargs["organisation_merge_record_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation_merge_record"] = self.organisation_merge_record

        confirmed_duplicates = [
            each for each in self.organisation_merge_record.potential_duplicates
        ]
        context["confirmed_duplicates"] = confirmed_duplicates

        confirmed_not_duplicates = [
            each for each in self.organisation_merge_record.potential_duplicates if each.status == 2
        ]
        context["confirmed_not_duplicates"] = confirmed_not_duplicates

        draft_merged_org = self.organisation_merge_record.get_draft_merged_organisation()
        context["draft_merged_org"] = draft_merged_org

        return context

    def form_valid(self, form):
        # let's merge the organisations
        self.organisation_merge_record.merge_organisations()

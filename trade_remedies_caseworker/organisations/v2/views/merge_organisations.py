from django.shortcuts import redirect
from django.urls import reverse

from config.base_views import BaseCaseWorkerTemplateView, BaseCaseWorkerView, FormInvalidMixin
from core.constants import SECURITY_GROUPS_TRA_ADMINS
from organisations.v2.forms import (
    CancelMergeForm,
    ConfirmNotDuplicateForm,
    MergeOrganisationsSelectDifferencesForm,
    ReviewMergeForm,
    SelectIfDuplicatesForm,
)


class ReviewMergeOrganisationView(BaseCaseWorkerTemplateView):
    template_name = "v2/merge_organisations/review_merge_organisation.html"

    def get_success_url(self):
        return self.request.GET.get(
            "redirect", self.request.META.get("HTTP_REFERER", reverse("cases"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client.invitations(self.kwargs["invitation_id"])
        context["invitation"] = invitation
        submission_organisation_merge_record = self.client.submission_organisation_merge_records(
            invitation.submission.id
        )
        context["submission_organisation_merge_record"] = submission_organisation_merge_record
        context[
            "organisation_merge_record"
        ] = submission_organisation_merge_record.organisation_merge_record

        invited_organisation = self.client.organisations(invitation.contact.organisation)
        context["invited_organisation"] = invited_organisation

        return context


class ReviewMatchingOrganisationsView(BaseCaseWorkerTemplateView):
    template_name = "v2/merge_organisations/review_matching_organisations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission_organisation_merge_record = self.client.submission_organisation_merge_records(
            self.kwargs["submission_organisation_merge_record_id"]
        )
        organisation_merge_record = submission_organisation_merge_record.organisation_merge_record

        context["submission_organisation_merge_record"] = submission_organisation_merge_record
        context["organisation_merge_record"] = organisation_merge_record
        context["duplicate_organisations"] = organisation_merge_record.potential_duplicates

        current_duplicate_index = int(self.request.GET.get("current_duplicate_index", 0))
        try:
            current_duplicate = organisation_merge_record.potential_duplicates[
                current_duplicate_index
            ]
        except IndexError:
            current_duplicate = organisation_merge_record.potential_duplicates[0]
            current_duplicate_index = 0
        context["current_duplicate_index"] = current_duplicate_index

        parent_organisation = self.client.organisations(
            organisation_merge_record.parent_organisation.id
        ).organisation_card_data()
        current_duplicate_organisation = self.client.organisations(
            current_duplicate.child_organisation.id
        ).organisation_card_data()

        context["parent_organisation"] = parent_organisation
        context["current_duplicate_organisation"] = current_duplicate_organisation
        context["identical_fields"] = current_duplicate.identical_fields

        next = True
        previous = False
        if current_duplicate_index > 0:
            previous = current_duplicate_index - 1

        if current_duplicate_index == len(organisation_merge_record.potential_duplicates) - 1:
            next = False

        context["next"] = next
        context["previous"] = previous

        context["user_in_required_groups"] = self.request.user.has_group(SECURITY_GROUPS_TRA_ADMINS)

        return context


class SelectDifferencesLooperView(BaseCaseWorkerView):
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def dispatch(self, request, *args, **kwargs):
        submission_organisation_merge_record = self.client.submission_organisation_merge_records(
            self.kwargs["submission_organisation_merge_record_id"]
        )
        organisation_merge_record = submission_organisation_merge_record.organisation_merge_record
        # find out if there are any pending duplicates to be reviewed
        pending_duplicate_review = next(
            (
                potential_duplicate
                for potential_duplicate in organisation_merge_record.potential_duplicates
                if potential_duplicate.status == "pending"
            ),
            None,
        )

        if pending_duplicate_review:
            # there's still a pending duplicate to review, redirect to that
            # first we make sure the status of the SubmissionOrganisationMergeRecord is
            # 'in progress'
            submission_organisation_merge_record.update({"status": "in_progress"})

            return redirect(
                reverse(
                    "organisations:merge_organisations_select_if_duplicate",
                    kwargs={
                        "duplicate_organisation_merge_id": pending_duplicate_review.id,
                        "submission_organisation_merge_record_id": submission_organisation_merge_record.id,
                    },
                )
            )
        # there's none left! redirect to the next step (review)
        submission_organisation_merge_record.update({"status": "complete"})
        return redirect(
            reverse(
                "organisations:merge_organisations_review",
                kwargs={
                    "submission_organisation_merge_record_id": submission_organisation_merge_record.id
                },
            )
        )


class BaseDifferencesView(BaseCaseWorkerTemplateView, FormInvalidMixin):
    """A base view for the select differences views, abstracts some of the common functionality
    involved in creating a draft phantom organisation and finding the identical fields between that
    and the chosen organisation to merge.
    """

    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def dispatch(self, request, *args, **kwargs):
        self.duplicate_organisation_merge = self.client.duplicate_organisation_merges(
            self.kwargs["duplicate_organisation_merge_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.duplicate_organisation_merge.order_in_parent[0] == 0:
            # if this is the first loop, nothing has been selected yet. The draft organisation
            # is the real parent organisation
            phantom_parent_organisation = self.duplicate_organisation_merge.parent_organisation
            identical_fields = self.duplicate_organisation_merge.identical_fields
        else:
            phantom_parent_organisation_and_identical_fields = (
                self.client.organisation_merge_records(
                    self.duplicate_organisation_merge.merge_record,
                ).get_draft_merged_selections(
                    current_duplicate_id=self.duplicate_organisation_merge.id
                )
            )
            phantom_parent_organisation = phantom_parent_organisation_and_identical_fields[
                "phantom_organisation_serializer"
            ]
            identical_fields = phantom_parent_organisation_and_identical_fields["identical_fields"]

        context["draft_parent_organisation"] = phantom_parent_organisation
        context["child_organisation"] = self.duplicate_organisation_merge.child_organisation
        context["duplicate_organisation_merge"] = self.duplicate_organisation_merge
        context["identical_fields"] = identical_fields
        return context


class SelectIfDuplicateView(BaseDifferencesView):
    form_class = SelectIfDuplicatesForm
    template_name = "v2/merge_organisations/select_if_duplicate.html"

    def form_valid(self, form):
        # updating the status of the DuplicateOrganisationMerge object
        if form.cleaned_data["is_matching_organisation_a_duplicate"]:
            self.duplicate_organisation_merge.update({"status": "confirmed_duplicate"})
            # now we ask the caseworker to select differences
            return redirect(
                reverse(
                    "organisations:merge_organisations_select_differences",
                    kwargs={
                        "duplicate_organisation_merge_id": self.duplicate_organisation_merge.id,
                        "submission_organisation_merge_record_id": self.kwargs[
                            "submission_organisation_merge_record_id"
                        ],
                    },
                )
            )
        else:

            # let's ask them to confirm the organisation is not a duplicate
            return redirect(
                reverse(
                    "organisations:merge_organisations_confirm_not_duplicate",
                    kwargs={
                        "duplicate_organisation_merge_id": self.duplicate_organisation_merge.id,
                        "submission_organisation_merge_record_id": self.kwargs[
                            "submission_organisation_merge_record_id"
                        ],
                    },
                )
            )


class ConfirmNotDuplicateView(BaseCaseWorkerTemplateView, FormInvalidMixin):
    template_name = "v2/merge_organisations/confirm_not_duplicate.html"
    form_class = ConfirmNotDuplicateForm
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def form_valid(self, form):
        duplicate_organisation_merge = self.client.duplicate_organisation_merges(
            self.kwargs["duplicate_organisation_merge_id"]
        )

        # update the status in the DB so this org is not checked again
        duplicate_organisation_merge.update({"status": "confirmed_not_duplicate"})

        # redirect to the looper
        return redirect(
            reverse(
                "organisations:merge_organisations_select_differences_looper",
                kwargs={
                    "submission_organisation_merge_record_id": self.kwargs[
                        "submission_organisation_merge_record_id"
                    ]
                },
            )
        )


class SelectDifferencesView(BaseDifferencesView):
    template_name = "v2/merge_organisations/select_differences.html"
    form_class = MergeOrganisationsSelectDifferencesForm

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
                "status": "attributes_selected",
            }
        )

        return redirect(
            reverse(
                "organisations:merge_organisations_select_differences_looper",
                kwargs={
                    "submission_organisation_merge_record_id": self.kwargs[
                        "submission_organisation_merge_record_id"
                    ]
                },
            )
        )


class ReviewMergeView(BaseCaseWorkerView, FormInvalidMixin):
    template_name = "v2/merge_organisations/review_merge.html"
    form_class = ReviewMergeForm
    groups_required = SECURITY_GROUPS_TRA_ADMINS

    def dispatch(self, request, *args, **kwargs):
        self.submission_organisation_merge_record = (
            self.client.submission_organisation_merge_records(
                self.kwargs["submission_organisation_merge_record_id"]
            )
        )
        self.organisation_merge_record = (
            self.submission_organisation_merge_record.organisation_merge_record
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation_merge_record"] = self.organisation_merge_record
        context["submission_organisation_merge_record"] = self.submission_organisation_merge_record

        confirmed_duplicates = [
            each
            for each in self.organisation_merge_record.potential_duplicates
            if each.status == "attributes_selected"
        ]
        confirmed_duplicates = self.client.organisations.get_organisation_cards(
            *[each.child_organisation.id for each in confirmed_duplicates]
        )
        context["confirmed_duplicates"] = confirmed_duplicates

        confirmed_not_duplicates = [
            each
            for each in self.organisation_merge_record.potential_duplicates
            if each.status == "confirmed_not_duplicate"
        ]
        confirmed_not_duplicates = self.client.organisations.get_organisation_cards(
            *[each.child_organisation.id for each in confirmed_not_duplicates]
        )
        context["confirmed_not_duplicates"] = confirmed_not_duplicates

        draft_merged_org = (
            self.call_client(timeout=100)
            .organisation_merge_records(self.organisation_merge_record.id)
            .get_draft_merged_organisation()
        )
        context["draft_merged_org"] = draft_merged_org

        return context

    def form_valid(self, form):
        # let's merge the organisations
        self.client.organisation_merge_records(
            self.organisation_merge_record.id
        ).merge_organisations()
        return redirect(
            reverse(
                "organisations:merge_organisations_merge_complete",
                kwargs={
                    "case_id": self.submission_organisation_merge_record.submission.case.id,
                    "submission_id": self.submission_organisation_merge_record.submission.id,
                },
            )
        )


class CancelMergeView(BaseCaseWorkerTemplateView, FormInvalidMixin):
    template_name = "v2/merge_organisations/cancel_merge.html"
    form_class = CancelMergeForm

    def form_valid(self, form):
        submission_organisation_merge_record = self.client.submission_organisation_merge_records(
            self.kwargs["submission_organisation_merge_record_id"]
        )

        for (
            duplicate_organisation
        ) in submission_organisation_merge_record.organisation_merge_record.potential_duplicates:
            self.client.duplicate_organisation_merges(duplicate_organisation.id).update(
                {"status": "pending"}
            )

        submission_organisation_merge_record.update({"status": "not_started"})
        return redirect(
            reverse(
                "organisations:merge_organisations_review_matching_organisations",
                kwargs={
                    "submission_organisation_merge_record_id": submission_organisation_merge_record.id
                },
            )
        )
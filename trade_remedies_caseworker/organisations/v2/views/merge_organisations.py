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


class ReviewPotentialDuplicatesLanding(BaseCaseWorkerTemplateView):
    template_name = "v2/merge_organisations/review_merge_organisation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.call_client(timeout=35)
        invitation = client.invitations(
            self.kwargs["invitation_id"],
            fields=[
                "contact",
                "submission",
                "created_by",
                "organisation",
                "organisation_name",
                "case",
            ],
        )
        context["invitation"] = invitation
        submission_organisation_merge_record = client.submission_organisation_merge_records(
            invitation.submission.id, params={"organisation_id": invitation.contact.organisation}
        )
        context["submission_organisation_merge_record"] = submission_organisation_merge_record
        context[
            "organisation_merge_record"
        ] = submission_organisation_merge_record.organisation_merge_record

        invited_organisation = client.organisations(
            invitation.contact.organisation, fields=["name"]
        )
        context["invited_organisation"] = invited_organisation

        self.request.session["invitation_id"] = self.kwargs["invitation_id"]
        self.request.session.modified = True

        return context


class ExitMergeOrganisationsView(BaseCaseWorkerView):
    def get(self, request, *args, **kwargs):
        submission_organisation_merge_record = self.client.submission_organisation_merge_records(
            self.kwargs["submission_organisation_merge_record_id"]
        )
        # if there's only 1 duplicate, update the status of the SubmissionMergeRecord
        # to 'not_started'
        if (
            len(submission_organisation_merge_record.organisation_merge_record.potential_duplicates)
            == 1
        ):
            submission_organisation_merge_record.update({"status": "not_started"})
        invitation_id = self.client.invitations(
            submission_id=submission_organisation_merge_record.submission.id,
            fields=["id"],
        )[0].id
        return redirect(
            reverse(
                "organisations:merge_organisations_review_potential_duplicates_landing",
                kwargs={"invitation_id": invitation_id},
            )
        )


class ReviewMatchingOrganisationsView(BaseCaseWorkerTemplateView):
    template_name = "v2/merge_organisations/review_matching_organisations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission_organisation_merge_record = self.call_client(
            timeout=30
        ).submission_organisation_merge_records(
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

        no_of_duplicates = len(organisation_merge_record.potential_duplicates)
        if no_of_duplicates >= 7:
            context["show_elipses"] = True
            # if there's more than 6 matches, paginate the results
            if current_duplicate_index == 0:
                # we're the start of the list
                context["pages"] = [0, 1, 2, "...", no_of_duplicates - 1]
            elif current_duplicate_index == no_of_duplicates - 1:
                # we're at the end of the list
                context["pages"] = [
                    0,
                    "...",
                    no_of_duplicates - 3,
                    no_of_duplicates - 2,
                    no_of_duplicates - 1,
                ]
            else:
                # we're somewhere in the middle
                context["pages"] = [0, "...", current_duplicate_index, "...", no_of_duplicates - 1]

        next = True
        previous = False
        if current_duplicate_index > 0:
            previous = current_duplicate_index - 1

        if current_duplicate_index == len(organisation_merge_record.potential_duplicates) - 1:
            next = False

        context["next"] = next
        context["previous"] = previous

        context["user_in_required_groups"] = self.request.user.has_group(SECURITY_GROUPS_TRA_ADMINS)
        if invitation_id := self.request.session.get("invitation_id"):
            context["invitation_landing_page_url"] = reverse(
                "organisations:merge_organisations_review_potential_duplicates_landing",
                kwargs={"invitation_id": invitation_id},
            )

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

        somr = submission_organisation_merge_record
        if pending_duplicate_review:
            # there's still a pending duplicate to review, redirect to that
            # first we make sure the status of the SubmissionOrganisationMergeRecord is
            # 'in progress'
            somr.update({"status": "in_progress"})

            return redirect(
                reverse(
                    "organisations:merge_organisations_select_if_duplicate",
                    kwargs={
                        "duplicate_organisation_merge_id": pending_duplicate_review.id,
                        "submission_organisation_merge_record_id": somr.id,
                    },
                )
            )
        # there's none left! redirect to the next step (review)
        somr.update({"status": "complete"})
        return redirect(
            reverse(
                "organisations:merge_organisations_review",
                kwargs={"submission_organisation_merge_record_id": somr.id},
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
        context["submission_organisation_merge_record_id"] = self.kwargs[
            "submission_organisation_merge_record_id"
        ]
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_radio_buttons = {}
        draft_parent_organisation = context["draft_parent_organisation"]
        child_organisation = context["child_organisation"]
        identical_fields = context["identical_fields"]
        duplicate_organisation_merge = context["duplicate_organisation_merge"]

        for key, value in draft_parent_organisation.items():
            child_value = getattr(child_organisation, key, None)
            if (
                duplicate_organisation_merge.child_fields
                and key in duplicate_organisation_merge.child_fields
            ):
                # the caseworker has previously selected they want the child's attribute
                selected_radio_buttons[key] = "child"
            elif (
                duplicate_organisation_merge.parent_fields
                and key in duplicate_organisation_merge.parent_fields
            ):
                # the caseworker has previously selected they want the parent's attribute
                selected_radio_buttons[key] = "parent"
            elif value in identical_fields:
                # the values are the same
                selected_radio_buttons[key] = "parent"
            elif value and not child_value:
                # data is in the parent, but not the child
                selected_radio_buttons[key] = "parent"
            elif not value and child_value:
                # data is in the child, but not the parent
                selected_radio_buttons[key] = "child"
            elif value and child_value:
                # data is in both, but not identical, select the parent by default
                selected_radio_buttons[key] = "parent"
            else:
                # data is in neither, select the parent by default
                selected_radio_buttons[key] = "parent"

        context["selected_radio_buttons"] = selected_radio_buttons
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
        self.submission_organisation_merge_record.update({"status": "complete"})
        return redirect(
            reverse(
                "organisations:merge_organisations_merge_complete",
                kwargs={
                    "case_id": self.submission_organisation_merge_record.submission.case.id,
                    "submission_id": self.submission_organisation_merge_record.submission.id,
                    "confirmed_duplicates": [
                        each
                        for each in self.organisation_merge_record.duplicate_organisations
                        if each["status"] == "confirmed_duplicate"
                    ],
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
                {
                    "status": "pending",
                    "parent_fields": [],
                    "child_fields": [],
                }
            )

        submission_organisation_merge_record.update({"status": "not_started"})
        somr = submission_organisation_merge_record
        return redirect(
            reverse(
                "organisations:merge_organisations_review_matching_organisations",
                kwargs={"submission_organisation_merge_record_id": somr.id},
            )
        )

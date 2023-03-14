import datetime
import json

from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from v2_api_client.shared.utlils import get_uploaded_loa_document

from cases.v2.forms import (
    AuthorisedSignatoryCreateNewContactForm,
    AuthorisedSignatoryForm,
    BeenAbleToVerifyRepresentativeForm,
    ExplainUnverifiedRepresentativeForm,
)
from config.base_views import BaseCaseWorkerTemplateView, FormInvalidMixin, TaskListView
from core.constants import CASE_ROLE_AWAITING_APPROVAL, CASE_ROLE_PREPARING, CASE_ROLE_REJECTED


class BaseOrganisationVerificationView(BaseCaseWorkerTemplateView):
    invitation_fields = []

    def dispatch(self, request, *args, **kwargs):
        if self.invitation_fields == "__all__":
            self.invitation = self.client.invitations(kwargs["invitation_id"])
        else:
            if "invitation_type" not in self.invitation_fields:
                self.invitation_fields.append("invitation_type")
            self.invitation = self.client.invitations(
                kwargs["invitation_id"], fields=self.invitation_fields
            )
        if not self.invitation.invitation_type == 2:
            # this is not a rep invite, raise 404
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.invitation
        return context


class OrganisationVerificationTaskListView(BaseOrganisationVerificationView, TaskListView):
    template_name = "v2/organisation_verification/tasklist.html"
    invitation_fields = "__all__"

    def dispatch(self, request, *args, **kwargs):
        # we need to check if the invited organisation has potential duplicates
        # if it does, we need to redirect to the potential duplicate's page
        # if not, we can continue with the task list
        response = super().dispatch(request, *args, **kwargs)
        submission_organisation_merge_record = self.client.submission_organisation_merge_records(
            self.invitation.submission.id,
            params={"organisation_id": self.invitation.contact.organisation},
        )
        if (
            submission_organisation_merge_record.status != "complete"
            and submission_organisation_merge_record.organisation_merge_record.status
            == "duplicates_found"
        ):
            return redirect(
                reverse(
                    "organisations:merge_organisations_review_potential_duplicates_landing",
                    kwargs={
                        "invitation_id": self.invitation.id,
                    },
                )
            )
        return response

    def get_task_list(self):
        steps = [
            {
                "heading": "Review representative",
                "sub_steps": [
                    {
                        "link": reverse(
                            "verify_organisation_verify_representative",
                            kwargs={"invitation_id": self.invitation.id},
                        ),
                        "link_text": "Representative",
                        "status": "Complete"
                        if self.invitation.submission.deficiency_notice_params
                        and "contact_org_verify"
                        in self.invitation.submission.deficiency_notice_params
                        else "Not Started",
                        "ready_to_do": True,
                    },
                    {
                        "link": reverse(
                            "verify_organisation_verify_letter_of_authority",
                            kwargs={"invitation_id": self.invitation.id},
                        ),
                        "link_text": "Letter of Authority",
                        "status": "Complete"
                        if self.invitation.authorised_signatory
                        else "Not Started",
                        "ready_to_do": True,
                    },
                ],
            },
            {
                "heading": "Confirm",
                "sub_steps": [
                    {
                        "link": reverse(
                            "verify_organisation_verify_confirm",
                            kwargs={"invitation_id": self.invitation.id},
                        )
                        if self.invitation.submission.deficiency_notice_params
                        and self.invitation.submission.deficiency_notice_params.get(
                            "contact_org_verify", False
                        )
                        else reverse(
                            "verify_organisation_verify_confirm_declined",
                            kwargs={"invitation_id": self.invitation.id},
                        ),
                        "link_text": "Submit decision",
                        "status": "Complete"
                        if self.invitation.approved_at or self.invitation.rejected_at
                        else "Not started yet",
                    },
                ],
            },
        ]
        return steps


class OrganisationVerificationVerifyRepresentative(
    BaseOrganisationVerificationView, FormInvalidMixin
):
    template_name = "v2/organisation_verification/verify_representative.html"
    form_class = BeenAbleToVerifyRepresentativeForm
    invitation_fields = ["contact", "organisation", "name", "email", "submission", "case"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invited_organisation = self.client.organisations(
            self.invitation.contact.organisation,
        )
        context["invited_organisation"] = invited_organisation
        context["invited_organisation_card"] = invited_organisation.organisation_card_data()
        context["inviter_organisation"] = self.client.organisations(self.invitation.organisation.id)

        organisation_case_roles = self.client.organisation_case_roles(
            organisation_id=self.invitation.contact.organisation
        )
        approved_roles = [
            each
            for each in organisation_case_roles
            if each.case_role_key
            not in [CASE_ROLE_AWAITING_APPROVAL, CASE_ROLE_REJECTED, CASE_ROLE_PREPARING]
        ]
        context["invited_approved_organisation_case_roles"] = approved_roles
        context["approved_representative_cases"] = [
            each for each in invited_organisation.representative_cases if each.validated
        ]

        # removing rejections from this case
        rejected_cases = [each for each in invited_organisation.rejected_cases]
        context["rejected_cases"] = rejected_cases
        context["last_rejection"] = (
            sorted(rejected_cases, key=lambda x: x.date_rejected)[0] if rejected_cases else None
        )

        context["rejected_representative_cases"] = [
            each for each in rejected_cases if each.type == "representative"
        ]
        context["rejected_interested_party_cases"] = [
            each for each in rejected_cases if each.type == "interested_party"
        ]

        context["number_of_approved_cases"] = len(
            approved_roles + context["approved_representative_cases"]
        )
        context["last_approval"] = (
            sorted(approved_roles, key=lambda x: x.validated_at)[0] if approved_roles else None
        )

        return context

    def form_valid(self, form):
        if form.cleaned_data["been_able_to_verify_representative"] == "True":
            self.client.submissions(self.invitation.submission.id).update(
                {
                    "deficiency_notice_params": json.dumps(
                        {
                            "contact_org_verify": True,
                            "contact_org_verify_at": datetime.datetime.now().isoformat(),
                            "contact_org_verify_by": self.request.user.email,
                        }
                    )
                },
                fields=["id"],
            )
            return redirect(
                reverse(
                    "verify_organisation_task_list",
                    kwargs={"invitation_id": self.invitation.id},
                )
            )
        else:
            self.client.submissions(self.invitation.submission.id).update(
                {
                    "deficiency_notice_params": json.dumps(
                        {
                            "contact_org_verify": False,
                            "contact_org_verify_at": datetime.datetime.now().isoformat(),
                            "contact_org_verify_by": self.request.user.email,
                        }
                    )
                },
                fields=["id"],
            )
            return redirect(
                reverse(
                    "verify_organisation_verify_explain_org_not_verified",
                    kwargs={"invitation_id": self.invitation.id},
                )
            )


class OrganisationVerificationVerifyLetterOfAuthority(
    BaseOrganisationVerificationView, FormInvalidMixin
):
    template_name = "v2/organisation_verification/verify_letter_of_authority.html"
    form_class = AuthorisedSignatoryForm
    invitation_fields = ["submission", "created_by", "organisation", "case", "authorised_signatory"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uploaded_loa_document"] = get_uploaded_loa_document(self.invitation.submission)
        return context

    def form_valid(self, form):
        if form.cleaned_data["authorised_signatory"] == "new_contact":
            # we want to create a new contact for this LOA
            return redirect(
                reverse(
                    "verify_organisation_verify_letter_of_authority_create_new_contact",
                    kwargs={"invitation_id": self.kwargs["invitation_id"]},
                )
            )
        else:
            self.invitation.update(
                {"authorised_signatory": form.cleaned_data["authorised_signatory"]}
            )

            return redirect(
                reverse(
                    "verify_organisation_task_list",
                    kwargs={"invitation_id": self.invitation.id},
                )
            )


class OrganisationVerificationVerifyLetterOfAuthorityCreateNewContact(
    OrganisationVerificationVerifyLetterOfAuthority
):
    form_class = AuthorisedSignatoryCreateNewContactForm
    invitation_fields = OrganisationVerificationVerifyLetterOfAuthority.invitation_fields + [
        "organisation_id"
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_new_contact"] = True
        return context

    def form_valid(self, form):
        # checking if the contact already exists
        if existing_contacts := self.client.contacts(email=form.cleaned_data["email"]):
            contact = existing_contacts[0]
        else:
            # a contact with that email cannot be found, create a new one
            contact = self.client.contacts(form.cleaned_data)
            # assigning them to the inviter's organisation
            contact.change_organisation(self.invitation.organisation_id)

        # assigning them to the case
        contact.add_to_case(case_id=self.invitation.case.id, primary=False)

        self.invitation.update({"authorised_signatory": contact.id})

        return redirect(
            reverse(
                "verify_organisation_task_list",
                kwargs={"invitation_id": self.invitation.id},
            )
        )


class OrganisationVerificationExplainUnverifiedRepresentativeView(
    BaseOrganisationVerificationView, FormInvalidMixin
):
    template_name = "v2/organisation_verification/explain_unverified_representative.html"
    form_class = ExplainUnverifiedRepresentativeForm
    invitation_fields = ["submission"]

    def form_valid(self, form):
        self.client.submissions(self.invitation.submission.id).update(
            {
                "deficiency_notice_params": json.dumps(
                    {
                        "explain_why_contact_org_not_verified": form.cleaned_data[
                            "explain_why_org_not_verified"
                        ]
                    }
                )
            },
            fields=["deficiency_notice_params"],
        )
        return redirect(
            reverse("verify_organisation_task_list", kwargs={"invitation_id": self.invitation.id})
        )


class OrganisationVerificationConfirmView(BaseOrganisationVerificationView):
    template_name = "v2/organisation_verification/confirm.html"
    invitation_fields = [
        "contact",
        "submission",
        "organisation_name",
        "created_by",
        "authorised_signatory",
    ]

    def post(self, request, *args, **kwargs):
        # the caseworker is approving this invite
        self.invitation.process_representative_invitation(approved=True)
        return redirect(
            reverse(
                "verify_organisation_verify_approved", kwargs={"invitation_id": self.invitation.id}
            )
        )


class OrganisationVerificationApprovedView(BaseOrganisationVerificationView):
    template_name = "v2/organisation_verification/approved.html"
    invitation_fields = ["case", "organisation_name", "contact"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inviters_name = self.invitation.organisation_name
        context["possessive_inviters_organisation_name"] = (
            f"{inviters_name}'" if inviters_name.endswith("s") else f"{inviters_name}'s"
        )
        return context


class OrganisationVerificationConfirmDeclinedView(BaseOrganisationVerificationView):
    template_name = "v2/organisation_verification/confirm.html"
    invitation_fields = [
        "contact",
        "submission",
        "organisation_name",
        "created_by",
        "authorised_signatory",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["declined"] = True
        return context

    def post(self, request, *args, **kwargs):
        # the caseworker is declining/rejecting the invite
        # self.client.submissions(self.invitation.submission.id).update_submission_status("deficient")
        self.invitation.process_representative_invitation(approved=False)
        return redirect(
            reverse(
                "verify_organisation_verify_declined", kwargs={"invitation_id": self.invitation.id}
            )
        )


class OrganisationVerificationDeclinedView(OrganisationVerificationApprovedView):
    template_name = "v2/organisation_verification/declined.html"

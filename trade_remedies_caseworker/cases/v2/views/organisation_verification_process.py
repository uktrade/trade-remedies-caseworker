import datetime
import json

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


class BaseOrganisationVerificationView(BaseCaseWorkerTemplateView):
    invitation_fields = []

    def dispatch(self, request, *args, **kwargs):
        self.invitation = self.client.invitations(
            kwargs["invitation_id"], fields=self.invitation_fields
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.invitation
        return context


class OrganisationVerificationTaskListView(BaseOrganisationVerificationView, TaskListView):
    template_name = "v2/organisation_verification/tasklist.html"

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
                        if self.invitation.submission.primary_contact
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
                        "status": "Not Started"
                        if self.invitation.submission.primary_contact
                        else "Cannot start yet",
                        "ready_to_do": True
                        if self.invitation.submission.primary_contact
                        else False,
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
    invitation_fields = ["contact", "organisation", "name", "email", "submission"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invited_organisation = self.client.organisations(self.invitation.contact.organisation)
        context["invited_organisation"] = invited_organisation
        context["inviter_organisation"] = self.client.organisations(self.invitation.organisation)

        organisation_case_roles = self.client.organisation_case_roles(
            organisation_id=self.invitation.contact.organisation
        )
        approved_roles = [each for each in organisation_case_roles if each.validated_at]
        context["invited_approved_organisation_case_roles"] = organisation_case_roles
        context["number_of_approved_cases"] = len(approved_roles)
        context["last_approval"] = (
            sorted(approved_roles, key=lambda x: x.validated_at)[0] if approved_roles else None
        )
        context["approved_representative_cases"] = [
            each for each in invited_organisation.representative_cases if each.validated
        ]

        # removing rejections from this case
        rejected_cases = [
            each
            for each in invited_organisation.rejected_cases
            if each.invitation_id != self.invitation.id
        ]
        context["rejected_cases"] = rejected_cases

        context["last_rejection"] = (
            sorted(rejected_cases, key=lambda x: x.date_rejected)[0]
            if invited_organisation.rejected_cases
            else None
        )

        seen_org_case_combos = []
        no_duplicate_user_cases = []
        for user_case in invited_organisation.user_cases:
            if (user_case.organisation.id, user_case.case.id) not in seen_org_case_combos:
                no_duplicate_user_cases.append(user_case)
                seen_org_case_combos.append((user_case.organisation.id, user_case.case.id))

        context["user_cases"] = no_duplicate_user_cases
        context["cases_acting_as_rep"] = [
            each
            for each in invited_organisation.case_contacts
            if each.organisation != invited_organisation.id
        ]

        return context

    def form_valid(self, form):
        if form.cleaned_data["been_able_to_verify_representative"] == "yes":
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
    invitation_fields = ["submission", "created_by", "organisation", "case"]

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
            self.client.submissions(self.invitation.submission.id).update(
                {"primary_contact": form.cleaned_data["authorised_signatory"]},
                fields=["primary_contact"],
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
        # creating a new contact
        new_contact = self.client.contacts(form.cleaned_data)

        # assigning them to the inviter's organisation
        new_contact.change_organisation(self.invitation.organisation_id)

        # assigning them to the case
        new_contact.add_to_case(case_id=self.invitation.case.id, primary=True)

        self.client.submissions(self.invitation.submission.id).update(
            {"primary_contact": new_contact.id}, fields=["primary_contact"]
        )

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
    invitation_fields = ["contact", "submission", "organisation_name", "created_by"]

    def post(self, request, *args, **kwargs):
        # the caseworker is approving this invite
        self.invitation.process_representative_invitation(approved=True)
        self.client.submissions(self.invitation.submission.id).update_submission_status("review_ok")
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
    invitation_fields = ["contact", "submission", "organisation_name", "created_by"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["declined"] = True
        return context

    def post(self, request, *args, **kwargs):
        # the caseworker is declining/rejecting the invite
        self.client.submissions(self.invitation.submission.id).update_submission_status("deficient")
        return redirect(
            reverse(
                "verify_organisation_verify_declined", kwargs={"invitation_id": self.invitation.id}
            )
        )


class OrganisationVerificationDeclinedView(OrganisationVerificationApprovedView):
    template_name = "v2/organisation_verification/declined.html"

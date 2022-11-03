from django.urls import reverse
from config.base_views import BaseCaseWorkerTemplateView, TaskListView
from organisations.v2.forms import EditOrganisationForm


class BaseOrganisationVerificationView(BaseCaseWorkerTemplateView):
    def dispatch(self, request, *args, **kwargs):
        self.invitation = self.client.invitations(kwargs["invitation_id"])
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
                "heading": "Review representative ",
                "sub_steps": [
                    {
                        "link": reverse(
                            "verify_organisation_verify_representative",
                            kwargs={"invitation_id": self.invitation.id},
                        ),
                        "link_text": "Representative",
                        "status": "Not Started",
                        "ready_to_do": True,
                    },
                    {
                        "link": reverse(
                            "verify_organisation_verify_letter_of_authority",
                            kwargs={"invitation_id": self.invitation.id},
                        ),
                        "link_text": "Letter of Authority",
                        "status": "Not Started",
                        "ready_to_do": True,
                    },
                ],
            },
        ]
        return steps


class OrganisationVerificationVerifyRepresentative(BaseOrganisationVerificationView):
    template_name = "v2/organisation_verification/verify_representative.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_case_role_client = self.client.organisation_case_roles
        organisation_case_roles = org_case_role_client._get_many(
            org_case_role_client.url(
                org_case_role_client.get_base_endpoint(),
                params={"organisation_id": self.invitation.contact.organisation},
            )
        )
        approved_roles = [each for each in organisation_case_roles if each.validated_at]
        context["invited_organisation_case_roles"] = organisation_case_roles
        context["number_of_approved_cases"] = len(approved_roles)
        context["last_approval"] = sorted(approved_roles, key=lambda x: x.validated_at)[0]

        invited_organisation = self.client.organisations(self.invitation.contact.organisation)
        context["invited_organisation"] = invited_organisation

        seen_org_case_combos = []
        no_duplicate_user_cases = []
        for user_case in invited_organisation.user_cases:
            if (user_case.organisation.id, user_case.case.id) not in seen_org_case_combos:
                no_duplicate_user_cases.append(user_case)
                seen_org_case_combos.append((user_case.organisation.id, user_case.case.id))

        context["user_cases"] = no_duplicate_user_cases
        context["cases_acting_as_rep"] = [
            each
            for each in no_duplicate_user_cases
            if each.organisation.id != invited_organisation.id
        ]
        context["inviter_organisation"] = self.client.organisations(self.invitation.organisation)

        return context


class OrganisationVerificationVerifyLetterOfAuthority(BaseCaseWorkerTemplateView):
    form_class = EditOrganisationForm
    template_name = "v2/organisations/edit_organisation.html"

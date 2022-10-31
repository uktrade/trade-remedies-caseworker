from config.base_views import BaseCaseWorkerTemplateView


class OrganisationVerificationProcessView(BaseCaseWorkerTemplateView):
    template_name = "v2/organisation_verification/tasklist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation_case_role = self.client.organisation_case_roles.get_with_case_and_organisation(
            organisation_id=kwargs["organisation_id"],
            case_id=kwargs["case_id"],
        )[0]
        context["organisation_case_role"] = organisation_case_role


        return context


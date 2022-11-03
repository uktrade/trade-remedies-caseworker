from config.base_views import BaseCaseWorkerTemplateView, FormInvalidMixin
from organisations.v2.forms import EditOrganisationForm


class EditOrganisationView(FormInvalidMixin, BaseCaseWorkerTemplateView):
    template_name = "v2/organisations/edit_organisation.html"
    form_class = EditOrganisationForm

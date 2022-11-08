from django.shortcuts import redirect
from django.urls import reverse

from config.base_views import BaseCaseWorkerTemplateView, FormInvalidMixin
from organisations.v2.forms import EditOrganisationForm


class EditOrganisationView(FormInvalidMixin, BaseCaseWorkerTemplateView):
    template_name = "v2/organisations/edit_organisation.html"
    form_class = EditOrganisationForm

    def get_success_url(self):
        return self.request.GET.get(
            "redirect", self.request.META.get("HTTP_REFERER", reverse("cases"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.client.organisations(self.kwargs["organisation_id"])
        return context

    def form_valid(self, form):
        self.client.organisations(self.kwargs["organisation_id"]).update(form.cleaned_data)
        return super().form_valid(form=form)

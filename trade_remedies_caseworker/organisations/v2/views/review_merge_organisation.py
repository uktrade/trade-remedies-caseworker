from django.urls import reverse

from config.base_views import BaseCaseWorkerTemplateView, FormInvalidMixin
from organisations.v2.forms import ReviewMergeOrganisationForm


class ReviewMergeOrganisationView(FormInvalidMixin, BaseCaseWorkerTemplateView):
    template_name = "v2/organisations/review_merge_organisation.html"
    form_class = ReviewMergeOrganisationForm

    def get_success_url(self):
        return self.request.GET.get(
            "redirect", self.request.META.get("HTTP_REFERER", reverse("cases"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.client.organisations(self.kwargs["organisation_id"])
        context["invitation"] = self.client.invitations(self.kwargs["invitation_id"])
        return context

    def form_valid(self, form):
        return super().form_valid(form=form)

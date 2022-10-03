from config.forms import BaseYourEmployerForm, ValidationForm
from django import forms


class UKOrganisationInviteForm(ValidationForm):
    organisation_name = forms.CharField()
    organisation_address = forms.CharField()
    companies_house_id = forms.CharField()
    organisation_id = forms.CharField()
    # Need a field to match element id in the form html template to add error message
    company_search_container = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        # The user has entered something in the autocomplete box but not selected an option
        if (
            self.data.get("input-autocomplete")
            and not self.cleaned_data.get("organisation_name")
            and not self.cleaned_data.get("organisation_address")
            and not self.cleaned_data.get("companies_house_id")
            and not self.cleaned_data.get("organisation_id")
        ):
            self.add_error("company_search_container", "companies_house_not_selected")
        # Nothing has been entered by the user
        elif not self.data.get("input-autocomplete"):
            self.add_error("company_search_container", "companies_house_not_searched")
        else:
            return self.cleaned_data

from django import forms

from config.forms import ValidationForm


class EditOrganisationForm(ValidationForm):
    name = forms.CharField(error_messages={"required": "edit_organisation_no_organisation_name"})
    address = forms.CharField()
    post_code = forms.CharField()
    country = forms.CharField()
    companies_house_id = forms.CharField()
    organisation_website = forms.CharField(required=False)
    vat_number = forms.CharField(required=False)
    eori_number = forms.CharField(required=False)
    duns_number = forms.CharField(required=False)
from django import forms

from config.forms import ValidationForm


class EditOrganisationForm(ValidationForm):
    name = forms.CharField(error_messages={"required": "edit_organisation_no_organisation_name"})
    address = forms.CharField()
    post_code = forms.CharField(required=False)
    country = forms.CharField()
    companies_house_id = forms.CharField(required=False)
    organisation_website = forms.CharField(required=False)
    vat_number = forms.CharField(required=False)
    eori_number = forms.CharField(required=False)
    duns_number = forms.CharField(required=False)

    def clean(self):
        if not self.cleaned_data.get("companies_house_id") and not self.cleaned_data.get(
            "post_code"
        ):
            self.add_error(
                "post_code", "caseworker_review_invite_no_company_post_code_or_number_entered"
            )
            self.add_error(
                "companies_house_id",
                "caseworker_review_invite_no_company_post_code_or_number_entered",
            )
        return self.cleaned_data

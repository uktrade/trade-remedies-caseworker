from django import forms
from v2_api_client.shared.fields import RequiredYesNoRadioButton

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


class MergeOrganisationsSelectDifferencesForm(ValidationForm):
    name = forms.CharField(required=False)
    address = forms.CharField(required=False)
    companies_house_id = forms.CharField(required=False)
    organisation_website = forms.CharField(required=False)
    vat_number = forms.CharField(required=False)
    eori_number = forms.CharField(required=False)
    duns_number = forms.CharField(required=False)


class ReviewMergeForm(ValidationForm):
    confirm = forms.BooleanField(error_messages={"required": "confirm_not_selected"}, required=True)

    def __init__(self, *args, **kwargs):
        self.confirmed_duplicates = kwargs.pop("confirmed_duplicates", [])
        super().__init__(*args, **kwargs)
        if not self.confirmed_duplicates:
            self.fields["confirm"].required = False


class SelectIfDuplicatesForm(ValidationForm):
    is_matching_organisation_a_duplicate = RequiredYesNoRadioButton(
        required=True,
        error_messages={"required": "is_matching_organisation_a_duplicate_no_selection"},
    )


class ConfirmNotDuplicateForm(ValidationForm):
    ...


class CancelMergeForm(ValidationForm):
    ...

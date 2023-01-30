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


class MergeOrganisationsSelectDifferencesForm(ValidationForm):
    name = forms.CharField(required=False)
    address = forms.CharField(required=False)
    companies_house_id = forms.CharField(required=False)
    organisation_website = forms.CharField(required=False)
    vat_number = forms.CharField(required=False)
    eori_number = forms.CharField(required=False)
    duns_number = forms.CharField(required=False)


class ReviewMergeForm(ValidationForm):
    confirm = forms.BooleanField(error_messages={"required": "confirm_not_selected"})


class SelectIfDuplicatesForm(ValidationForm):
    is_matching_organisation_a_duplicate = forms.NullBooleanField()


class ConfirmNotDuplicateForm(ValidationForm):
    ...


class CancelMergeForm(ValidationForm):
    ...

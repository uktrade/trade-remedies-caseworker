from config.forms import BaseYourEmployerForm, ValidationForm
from django import forms


class OrganisationInviteForm(ValidationForm):
    organisation_name = forms.CharField()
    organisation_address = forms.CharField()
    organisation_post_code = forms.CharField()
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
            and not self.cleaned_data.get("organisation_post_code")
            and not self.cleaned_data.get("companies_house_id")
            and not self.cleaned_data.get("organisation_id")
        ):
            self.add_error("company_search_container", "organisation_not_selected")
        # Nothing has been entered by the user
        elif not self.data.get("input-autocomplete"):
            self.add_error("company_search_container", "organisation_not_searched")
        else:
            return self.cleaned_data


class OrganisationInviteContactForm(ValidationForm):
    # declare empty choices variable
    choices = []

    def __init__(self, *args, **kwargs):
        org_invite_contacts = kwargs.pop("org_invite_contacts", None)
        super().__init__(*args, **kwargs)
        # assign value to the choices variable
        self.fields["which_contact"].choices = org_invite_contacts

    which_contact = forms.ChoiceField(
        error_messages={"required": "no_contact_selected"},
        choices=[],  # use the choices variable
    )


class OrganisationInviteContactNewForm(ValidationForm):
    organisation_name = forms.CharField(
        error_messages={"required": "invite_contact_no_organisation_name"}
    )
    contact_name = forms.CharField(error_messages={"required": "invite_contact_no_name"})
    contact_email = forms.EmailField(
        error_messages={
            "required": "invite_contact_no_email",
            "invalid": "invite_contact_invalid_email",
        }
    )


class OrganisationInviteContactReviewForm(ValidationForm):
    pass


class OrganisationInviteCompleteForm(ValidationForm):
    pass

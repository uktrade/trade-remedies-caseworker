from config.forms import ValidationForm
from django import forms


class OrganisationInviteForm(ValidationForm):
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


class OrganisationInviteContactForm(ValidationForm):
    # declare empty choices variable
    choices = []

    def __init__(self, *args, **kwargs):
        org_invite_contacts = kwargs.pop("org_invite_contacts", None)
        super(OrganisationInviteContactForm, self).__init__(*args, **kwargs)
        # assign value to the choices variable
        self.fields["which_contact"].choices = org_invite_contacts

    which_contact = forms.ChoiceField(
        error_messages={"required": "no_representative_org"},
        choices=[],  # use the choices variable
    )


class OrganisationInviteContactNewForm(ValidationForm):
    organisation_name = forms.CharField(
        error_messages={"required": "invite_new_representative_no_organisation_name"}
    )
    contact_name = forms.CharField(error_messages={"required": "no_contact_name_entered"})
    contact_email = forms.EmailField(
        error_messages={
            "required": "no_contact_email_entered",
            "invalid": "contact_email_not_valid",
        }
    )


class OrganisationInviteContactReviewForm(ValidationForm):
    pass


class OrganisationInviteCompleteForm(ValidationForm):
    pass
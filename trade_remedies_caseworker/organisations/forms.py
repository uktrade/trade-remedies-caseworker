from config.forms import ValidationForm
from django import forms


class OrganisationInviteForm(ValidationForm):
    # Need a field to match element id in the form html template to add error message
    organisation_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        # The user has selected an organisation (i.e. when JS is not working or disabled)
        if self.data.get("search-reg-org"):
            self.cleaned_data["organisation_id"] = self.data.get("search-reg-org")

            return self.cleaned_data

        # The user has entered something in the autocomplete box and/or not selected an option
        if self.data.get("input-autocomplete") and not self.cleaned_data.get("organisation_id"):
            self.add_error("organisation_id", "organisation_not_selected")
        # Nothing has been selected
        elif not self.data.get("search-reg-org") and not self.cleaned_data.get("organisation_id"):
            if "input-autocomplete" in self.data:
                # Nothing has been entered by the user
                self.add_error("organisation_id", "organisation_not_searched")
            else:
                # Nothing has been selected by the user (i.e. when JS is not working or disabled)
                self.add_error("organisation_id", "organisation_not_selected")
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
    contact_name = forms.CharField(
        error_messages={"required": "invite_contact_no_name"}  # /PS-IGNORE
    )
    contact_email = forms.EmailField(
        error_messages={
            "required": "invite_contact_no_email",
            "invalid": "invite_contact_invalid_email",
        }
    )

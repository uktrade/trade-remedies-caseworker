from django import forms

from config.forms import ValidationForm


class BeenAbleToVerifyRepresentativeForm(ValidationForm):
    been_able_to_verify_representative = forms.ChoiceField(
        error_messages={
            "required": "verify_invite_no_option_selected",
        },
        choices=(
            ("True", True),
            ("False", False),
        ),
    )


class ExplainUnverifiedRepresentativeForm(ValidationForm):
    explain_why_org_not_verified = forms.CharField()


class AuthorisedSignatoryForm(ValidationForm):
    authorised_signatory = forms.CharField(
        error_messages={"required": "caseworker_review_invite_no_contact_selected"}
    )


class AuthorisedSignatoryCreateNewContactForm(ValidationForm):
    name = forms.CharField(
        error_messages={"required": "caseworker_review_invite_new_contact_no_name"}
    )
    email = forms.EmailField(
        error_messages={
            "required": "caseworker_review_invite_new_contact_no_email",
            "invalid": "caseworker_review_invite_new_contact_incorrect_email",
        }
    )

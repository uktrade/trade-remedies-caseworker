from django import forms

from config.forms import ValidationForm


class BeenAbleToVerifyRepresentativeForm(ValidationForm):
    been_able_to_verify_representative = forms.ChoiceField(
        error_messages={
            "required": "edit_organisation_no_organisation_name",
        },
        choices=(
            ("yes", True),
            ("no", False),
        ),
    )


class ExplainUnverifiedRepresentativeForm(ValidationForm):
    explain_why_org_not_verified = forms.CharField()

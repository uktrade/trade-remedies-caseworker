from config.forms import ValidationForm
from config.forms.fields import CharField


class EditOrganisationForm(ValidationForm):
    name_of_organisation = CharField(label="Name of organisation")

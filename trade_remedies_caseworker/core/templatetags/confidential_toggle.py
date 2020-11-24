from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Present a confidential indicator
Usage:
    {{ confidential_toggle document }}

"""


@register.simple_tag
def confidential_toggle(document, tab=None):
    if document.get("type", {}).get("key") != "respondent":
        label = "Yes" if document["confidential"] else "No"
        return mark_safe(
            f"""<button
                    type="button"
                    class="button-link toggle-confidential"
                    data-tab="{tab}"
                    data-document_id="{document['id']}"
                    data-confidential="{document['confidential']}">{label}</button>"""
        )
    else:
        return "Yes" if document["confidential"] else "No"

from core.templatetags import register
from django.utils.safestring import mark_safe
from html import escape


"""
Template tag to display a document download link if applicable or just the document name if not
Usage:
    {% document_link document %}
"""


@register.simple_tag()
def document_link(document, with_link=True, with_confidential_mark=False):
    _link = ["", escape(document.get("name")), ""]
    safe = document.get("safe")
    if safe and with_link:
        _link[
            0
        ] = f"""<a href="/document/{document['id']}/download/" class="link" target="_blank">"""
        _link[2] = "</a>"
    elif (safe is None) and with_link:
        _link[
            0
        ] = f'<i class="icon icon-amber-warning correct margin-right-5px" title="This file has not yet been scanned for viruses"></i>'
    elif safe is False:
        _link[
            0
        ] = '<i class="icon icon-skull correct margin-right-5px" title="This file is infected with a virus"></i>'
    if safe and with_confidential_mark:
        _link.append(" (confidential)" if document.get("confidential") else " (non-confidential)")
    return mark_safe("".join(_link))

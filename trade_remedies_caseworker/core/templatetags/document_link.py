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
    if with_link:
        _link[
            0
        ] = f"""<a href="/document/{document['id']}/download/" class="link" target="_blank">"""
        _link[2] = "</a>"
    if with_confidential_mark:
        _link.append(" (confidential)" if document.get("confidential") else " (non-confidential)")
    return mark_safe("".join(_link))

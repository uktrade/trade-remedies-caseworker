from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag(takes_context=True)
def text_element(
    context,
    id,
    label,
    errors=None,
    data_mode=None,
    name=None,
    textarea=None,
    value=None,
    hint=None,
    password=False,
    readonly=False,
    autocomplete=None,
):
    """
    Display one or more error messages
    """
    output = []
    type = "password" if password else "text"
    readonly = "readonly" if readonly else ""
    if autocomplete:
        autocomplete = f'autocomplete="{autocomplete}" '
    else:
        autocomplete = ""
    if value is None:
        value = context.get(id, "")
    output.append('<div class="form-group type-text ')
    if id and errors and id in errors:
        output.append("form-group-error ")
    output.append('"')
    if data_mode:
        output.append(' data-attach="Typeahead"')
    output.append(">")
    output.append(f'<label class="form-label" for="{ id }">{ label }')
    if hint:
        output.append(f'<span class="form-hint">{ hint }</span>')
    output.append("</label>")
    name = name or id
    if name and errors and name in errors:
        message = errors[name]
        output.append(f'<span class="error-message" id="{ name }_error">{ message }</span>')
    if data_mode:  # for typeahead elements
        output.append(
            f'<input { autocomplete } class="form-control" id="{ id }" type="text" data-mode="{ data_mode }" name="{ name }" { readonly } value="{ value }">'  # noqa: E501
        )
    elif textarea:
        output.append(
            f'<textarea class="form-control" id="{ id }" name="{ name }" { readonly }>{ value }</textarea>'  # noqa: E501
        )
    else:
        output.append(
            f'<input { autocomplete }class="form-control" id="{ id }" type="{ type }" name="{ name }" value="{ value }" { readonly }>'  # noqa: E501
        )
    output.append("</div>")
    return mark_safe("".join(output))

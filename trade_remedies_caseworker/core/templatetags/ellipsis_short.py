from core.templatetags import register


@register.filter
def ellipsis_short(text, max_length=30):
    """
    Convert a long string (e.g. file name) into an ellipsis shorter version.
    For example:
        Application-dumping-countervailing-2_1_20180328111900_3_20180423135809.docx
        to
        Application-dumping...135809.docx
    """
    if len(text) > max_length:
        char_len = max_length - 3  # include ellipsis length
        half_point = int(char_len / 2)
        parts = [text[0:half_point]]
        parts.append("...")
        parts.append(text[-1 * (char_len - half_point):])
        return "".join(parts)
    else:
        return text

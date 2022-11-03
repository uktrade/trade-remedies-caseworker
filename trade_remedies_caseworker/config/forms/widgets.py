from django import forms


class TextInput(forms.TextInput):
    template_name = "v2/widgets/text_input.html"

    def render(self, name, value, attrs=None, renderer=None, bound_field=None):
        context = self.get_context(name, value, attrs, bound_field)
        return self._render(self.template_name, context, renderer)

    def get_context(self, name, value, attrs, bound_field):
        context = super().get_context(name, value, attrs)
        context["bound_field"] = bound_field
        return context

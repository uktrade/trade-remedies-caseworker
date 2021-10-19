from django.test import TestCase

from django.template import Template, Context
from django.utils.html import escape


class TestTextElement(TestCase):
    def test_value_is_escaped(self):
        img_tag_str = '<img src="test" />'

        rendered = Template(
            "{% load text_element %}"
            "{% text_element id='test' label='Test' value=img_tag_str %}"
        ).render(Context({"img_tag_str": img_tag_str}))

        assert escape(img_tag_str) in rendered
        assert rendered.count("src") == 1

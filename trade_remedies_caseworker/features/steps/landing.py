from behave import when

from features.api_test_objects import create_test_object


@when("test")
def create_acct_page(context):
    # Generate test objects
    create_test_object("case")

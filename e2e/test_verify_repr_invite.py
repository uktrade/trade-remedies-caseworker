import os
import pytest

from e2e.utils import get_base_url, retry, login_user

BASE_URL = get_base_url()

@retry()
@pytest.mark.order(3)
def test_verify_repr_invite(page):
    email = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")
    case_id = os.getenv("TEST_REPR_INVITE_CASE_ID")
    company_name = os.getenv("TEST_REPR_COMPANY_NAME")

    login_user(page, email, password, BASE_URL)

    page.wait_for_timeout(200)

    page.get_by_role("link", name=case_id).click()
    page.get_by_role("link", name="Parties").click()
    page.locator(f"a:has-text('{company_name}')").first.click()
    page.get_by_role("button", name="Verification process").click()
    page.locator(f"a:has-text('Verify {company_name}')").first.click()
    page.locator("input[name=\"deficiency_notice_params_org_verify\"]").nth(1).check()
    page.get_by_role("button", name="Save").click()
    page.locator("a:has-text('Choose to accept into case')").click()
    page.get_by_role("alert").locator("form div").filter(has_text=f"Do you want to accept {company_name.split()[0]}").nth(1).click()
    page.locator("#accepted-radio").check()
    page.get_by_role("combobox").select_option("domestic_producer")
    page.get_by_role("button", name="Save").click()
    page.get_by_role("button", name="OK").click()
    page.get_by_role("link", name="Notify contact").click()
    page.get_by_role("button", name="Send the notification").click()
    page.get_by_role("button", name="Exit").click()

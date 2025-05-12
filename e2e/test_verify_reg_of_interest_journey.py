import os
import pytest

from e2e.utils import get_base_url, retry, login_user

BASE_URL = get_base_url()

@retry()
@pytest.mark.order(2)
def test_verify_reg_interest_journey(page):
    
    email = os.environ.get("TEST_USER_EMAIL")
    password = os.environ.get("TEST_USER_PASSWORD")
    case_id = os.environ.get("TEST_REGISTER_INTEREST_CASE_ID")
    company_name = os.environ.get("TEST_REPR_COMPANY_NAME")

    login_user(page, email, password, BASE_URL)

    page.wait_for_timeout(200)

    page.get_by_role("link", name=case_id).click()

    # go to the reps menu
    page.locator("#menu-bar > div:nth-child(3)").click()

    page.locator(f"a:has-text('{company_name}')").first.click()
    
    page.get_by_role("link", name="Registration of Interest").click()
    page.get_by_role("button", name="Verification process").click()
    page.get_by_role("link", name=f"Verify {company_name}").click()
    page.locator("input[name=\"deficiency_notice_params_org_verify\"]").first.check()
    page.locator("input[name=\"deficiency_notice_params_org_verify\"]").nth(1).check()
    page.get_by_role("button", name="Save").click()
    page.get_by_role("link", name="Choose to accept into case").click()
    page.locator("#accepted-radio").check()
    page.get_by_role("combobox").select_option("domestic_producer")
    page.get_by_role("button", name="Save").click()
    page.get_by_role("button", name="OK").click()
    page.get_by_role("button", name="Exit").click()
    page.get_by_role("button", name="OK").click()
    page.get_by_text("Original information request6").click()
    page.get_by_role("link", name="Expand deficiency documents").click()
    page.get_by_role("button", name="Verification process").click()
    page.get_by_role("link", name="Notify contact").click()
    page.get_by_role("button", name="Send the notification").click()
    page.get_by_role("button", name="OK").click()
    page.get_by_role("button", name="Exit").click()

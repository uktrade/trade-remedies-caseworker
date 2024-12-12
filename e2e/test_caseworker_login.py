from playwright.sync_api import expect

from e2e.utils import get_base_url, retry

BASE_URL = get_base_url()

@retry()
def test_public_login(page):
    page.goto(f"{BASE_URL}")
    expect(page.get_by_role("link", name="Trade Remedies Authority")).to_be_visible()
    expect(page.get_by_role("button", name="Log in")).to_be_visible()
    expect(page.get_by_role("link", name="Forgotten password")).to_be_visible()
    expect(page.get_by_label("Email")).to_be_visible()
    expect(page.get_by_label("Password")).to_be_visible()

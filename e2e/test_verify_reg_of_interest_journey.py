import pytest

from playwright.sync_api import expect

from e2e.utils import get_base_url, retry

BASE_URL = get_base_url()

@retry()
@pytest.mark.order(2)
def test_verify_reg_interest_journey(page):
    pass

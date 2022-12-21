import uuid
import pytest
from unittest.mock import MagicMock

from .views import AuditView


@pytest.fixture
def audit_data():
    """Fake Audit data."""
    return ["Audit data"] * 100


@pytest.fixture
def case():
    """Fake case."""
    mock_case = MagicMock()
    mock_case.id = uuid.uuid4()
    return mock_case


@pytest.fixture
def api_client(monkeypatch, audit_data):
    """Fake API client."""
    mock_api = MagicMock()
    mock_api.get_audit = MagicMock(return_value=audit_data)
    return mock_api


@pytest.fixture
def audit_view(api_client, case):
    """Basic audit view."""
    view = AuditView()
    view._client = api_client
    view.request = MagicMock()
    view.limit = 20
    view.start = 0
    view.case_id = case.id
    return view


class TestAuditView:
    def test_add_page_data(self, audit_view, audit_data, case):
        audit_view.request.GET = {}
        result = audit_view.add_page_data()
        assert result["milestone"]
        assert result["events"] == audit_data
        assert result["next_url"] == f"/case/{case.id}/audit?milestone=true&start=20"
        assert result["prev_url"] is None

    def test_add_page_data_params(self, audit_view, case):
        audit_view.request.GET = {"milestone": "false", "limit": 50}
        result = audit_view.add_page_data()
        assert not result["milestone"]
        assert result["next_url"] == f"/case/{case.id}/audit?milestone=false&start=50"

    def test_add_page_data_middle_page(self, audit_view, case):
        audit_view.start = 40
        audit_view.request.GET = {}
        result = audit_view.add_page_data()
        assert result["next_url"] == f"/case/{case.id}/audit?milestone=true&start=60"
        assert result["prev_url"] == f"/case/{case.id}/audit?milestone=true&start=20"

    def test_add_page_data_middle_page_skewed(self, audit_view, case):
        audit_view.start = 25
        audit_view.request.GET = {"limit": 50}
        result = audit_view.add_page_data()
        assert result["next_url"] == f"/case/{case.id}/audit?milestone=true&start=75"
        assert result["prev_url"] == f"/case/{case.id}/audit?milestone=true&start=0"

    def test_add_page_data_one_page(self, audit_view, case):
        audit_view.start = 50
        audit_view.request.GET = {"limit": 150}
        result = audit_view.add_page_data()
        assert result["next_url"] is None
        assert result["prev_url"] is None

    def test_add_page_data_last_page(self, audit_view, case):
        audit_view.start = 75
        audit_view.request.GET = {"limit": 20}
        result = audit_view.add_page_data()
        assert result["next_url"] == f"/case/{case.id}/audit?milestone=true&start=95"
        assert audit_view.start == 95
        # Last page with just 5 items
        audit_view._client = MagicMock()
        audit_view._client.get_audit = MagicMock(return_value=["Audit data"] * 5)
        # Simulate clicking 'next'
        result = audit_view.add_page_data()
        assert result["next_url"] is None
        assert result["prev_url"] == f"/case/{case.id}/audit?milestone=true&start=75"

    def test_add_page_data_client_call(self, audit_view, case):
        audit_view.request.GET = {}
        audit_view.add_page_data()
        audit_view._client.get_audit.assert_called_with(
            case_id=case.id, start=0, limit=20, milestone=True
        )

    def test_add_page_data_client_call_params(self, audit_view, case):
        audit_view.request.GET = {"milestone": "false", "limit": 100}
        audit_view.add_page_data()
        audit_view._client.get_audit.assert_called_with(
            case_id=case.id, start=0, limit=100, milestone=False
        )

    def test_add_page_data_client_call_offset(self, audit_view, case):
        audit_view.request.GET = {}
        audit_view.start = 25
        audit_view.add_page_data()
        audit_view._client.get_audit.assert_called_with(
            case_id=case.id, start=25, limit=20, milestone=True
        )

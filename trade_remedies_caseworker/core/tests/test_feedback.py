import datetime
from django.test import TestCase

mock_feedback = {
    "verbose_rating_name": "Satisfied",
    "verbose_what_didnt_go_so_well": [
        "Process is not clear",
        "Not enough guidance",
        "I was asked for information I don’t have",
        "Other issue",
    ],
    "created_at": datetime.datetime(2022, 11, 24, 14, 19, 4),
    "last_modified": datetime.datetime(2022, 11, 24, 14, 19, 4),
    "logged_in": True,
    "rating": 4,
    "what_didnt_work_so_well": [
        "process_not_clear",
        "not_enough_guidance",
        "asked_for_info_didnt_have",
        "other_issue",
    ],
    "what_didnt_work_so_well_other": "crap",
    "how_could_we_improve_service": "really bad",
    "url": "/dashboard/",
    "journey": "Generic Header",
}


class TestFeedback(TestCase):
    """@patch("v2_api_client.client.TRSAPIClient")
    def test_export(self, mocked_trs_client):
        mocked_trs_client.feedback.return_value = [mock_feedback]
        self.client.force_login(TransientUser(
        username="test@example.com",  /PS-IGNORE
        token="test_token"
        ))
        response = self.client.get(reverse("export_feedback_objects"))
        print("asd")"""

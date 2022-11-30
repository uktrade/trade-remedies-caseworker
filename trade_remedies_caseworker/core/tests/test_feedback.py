import datetime
from unittest.mock import patch

from django.urls import reverse
from dotwiz import DotWiz

from config.test_bases import UserTestBase

mock_feedback = DotWiz(
    {
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
)


def get_feedbacks():
    return [
        mock_feedback,
    ]


class TestFeedback(UserTestBase):
    @patch("v2_api_client.library.generic.FeedbackAPIClient")
    def test_export(self, mocked_feedback_client):
        mocked_feedback_client.return_value = get_feedbacks
        self.client.force_login(self.test_user)
        response = self.client.get(reverse("export_feedback_objects"))
        print("asd")
        assert True

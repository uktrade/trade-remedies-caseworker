from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from trade_remedies_client.client import Client
from core.utils import get

SUBMISSION_TYPE_HELPERS = {}


class BaseSubmissionHelper:
    type_ids = None

    def __init__(self, submission, user):
        self.submission = submission
        self.case = submission["case"] if submission else None
        self.user = user

    def get_context(self):
        return {}

    def on_update(self, **kwargs):
        return None

    def on_approve(self, **kwargs):
        return None

    @property
    def client(self):
        try:
            return self._client
        except AttributeError:
            self._client = Client(self.user.token)
        return self._client


class InviteThirdPartySubmission(BaseSubmissionHelper):
    type_ids = []

    def get_context(self):
        invites = []
        case_id = self.case["id"]
        if self.submission:
            invites = self.client.get_third_party_invites(case_id, self.submission["id"])
        return {
            "invites": invites,
        }


class AssignUserSubmission(BaseSubmissionHelper):
    type_ids = []

    def get_context(self):
        representing = None
        if self.submission:
            representing = self.submission["organisation"]
        return {
            "representing": representing,
        }

    def on_approve(self, **kwargs):
        user_organisation_id = self.submission["contact"]["organisation"]["id"]
        if self.submission["organisation"]["id"] != user_organisation_id:
            # make the case assignment now.
            is_primary = (
                    self.submission.get("deficiency_notice_params", {})
                    .get("assign_user", {})
                    .get("contact_status")
                    == "primary"
            )
            self.client.assign_user_to_case(
                user_organisation_id=user_organisation_id,
                representing_id=self.submission["organisation"]["id"],
                user_id=self.submission["contact"]["user"]["id"],
                case_id=self.case["id"],
                primary=is_primary,
            )
        return {"alert": f'Assigned {get(self.submission, "contact/user/name")} to case'}


SUBMISSION_TYPE_HELPERS["invite"] = InviteThirdPartySubmission
SUBMISSION_TYPE_HELPERS["assign"] = AssignUserSubmission


def get_submission_deadline(submission, fmt=None):
    """Return the submission deadline.
    If the submission has the deficiency notice params (i.e., being set up)
    use those to determine due date.

    Arguments:
        submission {Submission} -- The Submission model instance

    Keyword Arguments:
        fmt {str} -- Datetime format for return value (default: {None})

    Returns:
        str -- Due date formatted as string
    """
    due_at = submission.get("due_at")
    dnp = submission.get("deficiency_notice_params") or {}
    if not dnp and due_at and isinstance(due_at, str):
        due_at = datetime.strptime(due_at, settings.API_DATETIME_FORMAT)
    else:
        time_window = (
                int(dnp.get("time_window") or "0") or int(submission.get("time_window") or "0") or 0
        )
        if time_window > 0:
            due_at = (timezone.now() + timedelta(days=time_window)).date()
    if fmt and due_at and not isinstance(due_at, str):
        due_at = due_at.strftime(fmt)
    return due_at

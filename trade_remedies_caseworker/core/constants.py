TRUTHFUL_INPUT_VALUES = ("true", "True", "TRUE", "1", "y", "Y", "yes", True)

CASE_PARTICIPANT_TYPES = [
    {"key": "applicant", "name": "Applicant", "add_link": "Add a complaining company"},
    {
        "key": "respondents",
        "name": "Responding interested parties",
        "add_link": "Add a responding party",
    },
    {
        "key": "observers",
        "name": "Observing interested parties",
        "add_link": "Add an observing party",
    },
    {
        "key": "self_identify",
        "name": "Self identified - awaiting approval",
        "add_link": "Add a self-identifying party",
    },
]

SECURITY_GROUP_SUPER_USER = "Super User"
SECURITY_GROUP_ORGANISATION_OWNER = "Organisation Owner"
SECURITY_GROUP_ORGANISATION_USER = "Organisation User"

SECURITY_GROUP_TRA_ADMINISTRATOR = "TRA Administrator"
SECURITY_GROUP_TRA_INVESTIGATOR = "TRA Investigator"
SECURITY_GROUP_TRA_LEAD_INVESTIGATOR = "Lead Investigator"
SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION = "Head of Investigation"

SECURITY_GROUPS_TRA = [
    SECURITY_GROUP_SUPER_USER,
    SECURITY_GROUP_TRA_ADMINISTRATOR,
    SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION,
    SECURITY_GROUP_TRA_LEAD_INVESTIGATOR,
    SECURITY_GROUP_TRA_INVESTIGATOR,
]

SECURITY_GROUPS_TRA_ADMINS = [
    SECURITY_GROUP_TRA_ADMINISTRATOR,
    SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION,
    SECURITY_GROUP_TRA_LEAD_INVESTIGATOR,
]

SECURITY_GROUPS_TRA_TOP_ADMINS = [
    SECURITY_GROUP_TRA_ADMINISTRATOR,
    SECURITY_GROUP_TRA_HEAD_OF_INVESTIGATION,
]

SUBMISSION_TYPE_REGISTER_INTEREST = 7
SUBMISSION_STATUS_INTEREST_SUFFICIENT = 21
SUBMISSION_STATUS_INTEREST_DEFICIENT = 22

SUBMISSION_TYPE_APPLICATION = 1
SUBMISSION_TYPE_QUESTIONNAIRE = 2
SUBMISSION_STATUS_QUESTIONNAIRE_SUFFICIENT = 8
SUBMISSION_STATUS_QUESTIONNAIRE_DEFICIENT = 9

SUBMISSION_TYPE_ADHOC = 3
SUBMISSION_STATUS_ADHOC_SUFFICIENT = 12
SUBMISSION_STATUS_ADHOC_DEFICIENT = 13

CASE_ROLE_AWAITING_APPROVAL = "awaiting_approval"
CASE_ROLE_REJECTED = "rejected"
CASE_ROLE_APPLICANT = "applicant"
CASE_ROLE_PREPARING = "preparing"

CASE_DOCUMENT_TYPE_LETTER_OF_AUTHORISATION = 2

# Notice types
SUBMISSION_NOTICE_TYPE_INVITE = "invite"
SUBMISSION_NOTICE_TYPE_DEFICIENCY = "deficiency"

# Submission direction weights
DIRECTION_BOTH = 0
DIRECTION_PUBLIC_TO_TRA = 1
DIRECTION_TRA_TO_PUBLIC = 2

# These case types allow no country selection
ALL_REGION_ALLOWED_TYPE_IDS = ["13", "16", "17", "18", "19", "20"]


# This maps keys to alert messages
ALERT_MAP = {
    "pass_conf": "Password does not match the confirmation",
    "pass_reset": "Could not reset password. Please try again",
}

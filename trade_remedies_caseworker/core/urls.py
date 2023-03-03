from django.conf import settings
from django.urls import path

from cases.views import SubmissionCreateView
from core.views import (
    AdminDebugToolsAssignOrganisationToCaseView,
    AdminDebugToolsCreateNewOrganisationView,
    AdminDebugToolsCreateNewUserView,
    AdminDebugToolsTestDuplicateFinding,
    AdminDebugToolsView,
    EditUserGroup,
    ExportFeedbackView,
    FeedbackFormExportView,
    FeedbackFormsView,
    FeedbackListView,
    SingleFeedbackView,
    SystemParameterSettings,
    ViewFeatureFlags,
    ViewOneFeatureFlag,
    AdminDebugToolsCreateNewContactView,
    AdminDebugToolsCreateNewInvitationView,
    AdminDebugToolsCreateNewInvitationSelectContactView,
)

urlpatterns = [
    path("bundles/create/", SubmissionCreateView.as_view(), name="create_submission"),
    path(
        "system_parameters/",
        SystemParameterSettings.as_view(),
        name="system_parameters",
    ),
    path("feedback/", FeedbackFormsView.as_view(), name="feedback_formes"),
    path(
        "feedback/<uuid:form_id>/",
        FeedbackFormsView.as_view(),
        name="fedback_form_view",
    ),
    path(
        "feedback/<uuid:form_id>/export/",
        FeedbackFormExportView.as_view(),
        name="form_export",
    ),
    path("feature_flags/", ViewFeatureFlags.as_view(), name="view_feature_flags"),
    path(
        "feature_flags/<str:feature_flag_name>",
        ViewOneFeatureFlag.as_view(),
        name="view_feature_one_flag",
    ),
    path("add_user_to_group/<str:group_name>/", EditUserGroup.as_view(), name="edit_user_group"),
    path("view_all_feedback/", FeedbackListView.as_view(), name="view_all_feedback"),
    path(
        "view_single_feedback/<uuid:feedback_id>",
        SingleFeedbackView.as_view(),
        name="view_single_feedback",
    ),
    path(
        "export_feedback_objects",
        ExportFeedbackView.as_view(),
        name="export_feedback_objects",
    ),
]

if settings.ADMIN_DEBUG_TOOLS_ENABLED:
    urlpatterns += [
        path("admin_debug_tools/", AdminDebugToolsView.as_view(), name="admin_debug_tools_landing"),
        path(
            "admin_debug_tools/create_new_organisation",
            AdminDebugToolsCreateNewOrganisationView.as_view(),
            name="admin_debug_tools_create_new_organisation",
        ),
        path(
            "admin_debug_tools/create_new_contact",
            AdminDebugToolsCreateNewContactView.as_view(),
            name="admin_debug_tools_create_new_contact",
        ),
        path(
            "admin_debug_tools/create_new_user",
            AdminDebugToolsCreateNewUserView.as_view(),
            name="admin_debug_tools_create_new_user",
        ),
        path(
            "admin_debug_tools/create_new_invitation",
            AdminDebugToolsCreateNewInvitationView.as_view(),
            name="admin_debug_tools_create_new_invitation",
        ),
        path(
            "admin_debug_tools/create_new_invitation_select_contact/"
            "<uuid:case_id>/<uuid:inviting_organisation_id>/",
            AdminDebugToolsCreateNewInvitationSelectContactView.as_view(),
            name="admin_debug_tools_create_new_invitation_select_contact",
        ),
        path(
            "admin_debug_tools/admin_debug_tools_assign_organisation_to_case",
            AdminDebugToolsAssignOrganisationToCaseView.as_view(),
            name="admin_debug_tools_assign_organisation_to_case",
        ),
        path(
            "admin_debug_tools/admin_debug_tools_check_duplicate_search",
            AdminDebugToolsTestDuplicateFinding.as_view(),
            name="admin_debug_tools_check_duplicate_search",
        ),
    ]

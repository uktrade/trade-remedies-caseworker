from django.urls import path
from core.views import (
    SystemParameterSettings,
    FeedbackFormsView,
    FeedbackFormExportView,
)
from cases.views import SubmissionCreateView

from trade_remedies_caseworker.core.views import AddUserToGroup, ViewFeatureFlags, \
    ViewOneFeatureFlag

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
    path(
        "feature_flags",
        ViewFeatureFlags.as_view(),
        name="view_feature_flags"
    ),
    path(
        "feature_flags/<str:feature_flag_name>",
        ViewOneFeatureFlag.as_view(),
        name="view_feature_one_flag"
    ),
    path(
        "add_user_to_group/<str:group_name>/<uuid:user_pk>",
        AddUserToGroup.as_view(),
        name="add_user_to_group"
    )
]

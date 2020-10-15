from django.urls import path
from core.views import (
    SystemParameterSettings,
    FeedbackFormsView,
    FeedbackFormExportView,
)
from cases.views import SubmissionCreateView

urlpatterns = [
    path("bundles/create/", SubmissionCreateView.as_view(), name="create_submission"),
    path("system_parameters/", SystemParameterSettings.as_view(), name="system_parameters"),
    path("feedback/", FeedbackFormsView.as_view(), name="feedback_formes"),
    path("feedback/<uuid:form_id>/", FeedbackFormsView.as_view(), name="fedback_form_view"),
    path("feedback/<uuid:form_id>/export/", FeedbackFormExportView.as_view(), name="form_export"),
]

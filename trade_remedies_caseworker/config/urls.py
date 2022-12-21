"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path

from cases.v2.views import organisation_verification_process
from cases.v2.views.organisation_verification_process import (
    OrganisationVerificationExplainUnverifiedRepresentativeView,
    OrganisationVerificationVerifyLetterOfAuthorityCreateNewContact,
)
from cases.views import CasesView
from core import views as core_views
from login import views as login_views
from password import views as password_views

urlpatterns = [
    path("", CasesView.as_view(), name="cases"),
    path("health/", core_views.HealthCheckView.as_view(), name="healthcheck"),
    path("accounts/login/", login_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", login_views.logout_view, name="logout"),
    path("system/", core_views.SystemView.as_view(), name="system"),
    path(
        "accounts/forgotpassword/done",
        password_views.ForgotPasswordRequested.as_view(),
        name="forgot_password_requested",
    ),
    path(
        "accounts/forgotpassword/",
        password_views.ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path(
        "accounts/password/reset/<uuid:user_pk>/<str:token>/",
        password_views.ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path("twofactor/", login_views.TwoFactorView.as_view(), name="2fa"),
    path("users/", include("users.urls")),
    path("case/", include("cases.urls")),
    path("cases/", include("cases.urls")),
    path(
        "organisationname/search/",
        core_views.OrganisationNameSearch.as_view(),
        name="organisationnamesearch",
    ),
    path("settings/", include("core.urls")),
    path("documents/", include("documents.urls")),
    path("document/", include("documents.urls")),
    path("organisations/", include("organisations.urls")),
    path("organisation/", include("organisations.urls")),
    path("companieshouse/search/", core_views.CompaniesHouseSearch.as_view()),
    path("tasks/", include("tasks.urls")),
]

urlpatterns += [
    path(
        "verify_organisation_start/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationTaskListView.as_view(),
        name="verify_organisation_task_list",
    ),
    path(
        "verify_organisation_verify_representative/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationVerifyRepresentative.as_view(),
        name="verify_organisation_verify_representative",
    ),
    path(
        "verify_organisation_verify_letter_of_authority/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationVerifyLetterOfAuthority.as_view(),
        name="verify_organisation_verify_letter_of_authority",
    ),
    path(
        "verify_organisation_verify_explain_org_not_verified/<uuid:invitation_id>/",
        OrganisationVerificationExplainUnverifiedRepresentativeView.as_view(),
        name="verify_organisation_verify_explain_org_not_verified",
    ),
    path(
        "verify_organisation_verify_letter_of_authority_create_new_contact/<uuid:invitation_id>/",
        OrganisationVerificationVerifyLetterOfAuthorityCreateNewContact.as_view(),
        name="verify_organisation_verify_letter_of_authority_create_new_contact",
    ),
    path(
        "verify_organisation_verify_confirm/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationConfirmView.as_view(),
        name="verify_organisation_verify_confirm",
    ),
    path(
        "verify_organisation_verify_approved/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationApprovedView.as_view(),
        name="verify_organisation_verify_approved",
    ),
    path(
        "verify_organisation_verify_confirm_declined/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationConfirmDeclinedView.as_view(),
        name="verify_organisation_verify_confirm_declined",
    ),
    path(
        "verify_organisation_verify_declined/<uuid:invitation_id>/",
        organisation_verification_process.OrganisationVerificationDeclinedView.as_view(),
        name="verify_organisation_verify_declined",
    ),
]

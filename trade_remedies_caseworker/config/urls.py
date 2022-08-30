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
from core import views as core_views
from cases.views import CasesView
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
        "companieshouse/search/", core_views.CompaniesHouseSearch.as_view(), name="companieshouse"
    ),
    path("settings/", include("core.urls")),
    path("documents/", include("documents.urls")),
    path("document/", include("documents.urls")),
    path("organisations/", include("organisations.urls")),
    path("organisation/", include("organisations.urls")),
    path("companieshouse/search/", core_views.CompaniesHouseSearch.as_view()),
    path("tasks/", include("tasks.urls")),
]

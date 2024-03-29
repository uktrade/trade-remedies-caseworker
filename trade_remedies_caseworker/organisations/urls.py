from django.urls import path
from django.views.generic import TemplateView

from organisations.v2.views import (
    caseworker_invite,
    edit_organisation,
    merge_organisations,
    adhoc_organisation_merge,
)
from organisations.views import (
    ContactDeleteView,
    ContactFormView,
    ContactPrimaryView,
    OrganisationCaseRoleView,
    OrganisationDedupeView,
    OrganisationDeleteView,
    OrganisationDuplicatesView,
    OrganisationFormView,
    OrganisationMatchView,
    OrganisationMergeView,
    OrganisationRemoveView,
    OrganisationView,
    OrganisationsView,
    ToggleOrganisationNonResponsiveView,
    ToggleOrganisationSampledView,
    ToggleUserAdmin,
)

app_name = "organisations"
urlpatterns = [
    path("", OrganisationsView.as_view(), name="organisations"),
    path("<uuid:organisation_id>/", OrganisationView.as_view(), name="v1_view_organisation"),
    path(
        "case/<uuid:case_id>/create/<str:organisation_type>/",
        OrganisationFormView.as_view(),
        name="create_organisation",
    ),
    path(
        "case/<uuid:case_id>/<str:organisation_type>/organisation/<uuid:organisation_id>/",
        OrganisationFormView.as_view(),
        name="create_organisation",
    ),
    path(
        "<uuid:organisation_id>/edit/",
        OrganisationFormView.as_view(),
        name="edit_organisation",
    ),
    path(
        "<uuid:organisation_id>/case/<uuid:case_id>/sampled/",
        ToggleOrganisationSampledView.as_view(),
        name="toggle_samples",
    ),
    path(
        "<uuid:organisation_id>/case/<uuid:case_id>/nonresponsive/",
        ToggleOrganisationNonResponsiveView.as_view(),
        name="toggle_nonresponsive",
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/contact/add/",
        ContactFormView.as_view(),
        name="add_contact",
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/contact/<uuid:contact_id>/",
        ContactFormView.as_view(),
        name="edit_contact",
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/contact/<uuid:contact_id>/delete/",
        ContactDeleteView.as_view(),
        name="delete_contact",
    ),
    path(
        "<uuid:organisation_id>/user/<uuid:user_id>/admin/toggle/",
        ToggleUserAdmin.as_view(),
        name="toggle_user_admin",
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/delete/",
        OrganisationDeleteView.as_view(),
        name="delete_organisation",
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/remove_from_case/",
        OrganisationRemoveView.as_view(),
        name="remove_organisation",
    ),
    path(
        "<uuid:organisation_id>/delete/",
        OrganisationDeleteView.as_view(),
        name="delete_organisation",
    ),
    path(
        "<uuid:organisation_id>/merge/",
        OrganisationMergeView.as_view(),
        name="merge_organisation",
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/change/",
        OrganisationCaseRoleView.as_view(),
    ),
    path(
        "case/<uuid:case_id>/organisation/<uuid:organisation_id>/contact/"
        "<uuid:contact_id>/set/primary/",
        ContactPrimaryView.as_view(),
        name="set_primary_contact",
    ),
    path(
        "<uuid:organisation_id>/case/<uuid:case_id>/role/",
        OrganisationCaseRoleView.as_view(),
        name="org_case_role",
    ),
    path(
        "<uuid:organisation_id>/duplicates/",
        OrganisationDuplicatesView.as_view(),
        name="match",
    ),
    path("dedupe/", OrganisationDedupeView.as_view(), name="dedupe"),
    path("match/", OrganisationMatchView.as_view(), name="match"),
]

urlpatterns += [
    path(
        "v2/edit/<uuid:organisation_id>/",
        edit_organisation.EditOrganisationView.as_view(),
        name="v2_edit_organisation",
    ),
]

# caseworker invite URLS
urlpatterns += [
    path(
        "case/<uuid:case_id>/invite/invite-party/",
        caseworker_invite.OrganisationInviteView.as_view(),
        name="invite-party",
    ),
    path(
        "case/<uuid:case_id>/invite/<uuid:organisation_id>/invite-party-contacts-choice",
        caseworker_invite.OrganisationInviteContactsView.as_view(),
        name="invite-party-contacts-choice",
    ),
    path(
        "case/<uuid:case_id>/invite/invite-party-contact-new",
        caseworker_invite.OrganisationInviteContactNewView.as_view(),
        name="invite-party-contact-new",
    ),
    path(
        "case/<uuid:case_id>/invite/<uuid:organisation_id>/invite-party-check",
        caseworker_invite.OrganisationInviteReviewView.as_view(),
        name="invite-party-check",
    ),
    path(
        "case/<uuid:case_id>/invite/invite-party-complete",
        caseworker_invite.OrganisationInviteCompleteView.as_view(),
        name="invite-party-complete",
    ),
]

urlpatterns += [
    path(
        "v2/edit/<uuid:organisation_id>/",
        edit_organisation.EditOrganisationView.as_view(),
        name="v2_edit_organisation",
    ),
]

# caseworker invite URLS
urlpatterns += [
    path(
        "case/<uuid:case_id>/invite/invite-party/",
        caseworker_invite.OrganisationInviteView.as_view(),
        name="invite-party",
    ),
    path(
        "case/<uuid:case_id>/invite/<uuid:organisation_id>/invite-party-contacts-choice",
        caseworker_invite.OrganisationInviteContactsView.as_view(),
        name="invite-party-contacts-choice",
    ),
    path(
        "case/<uuid:case_id>/invite/invite-party-contact-new",
        caseworker_invite.OrganisationInviteContactNewView.as_view(),
        name="invite-party-contact-new",
    ),
    path(
        "case/<uuid:case_id>/invite/<uuid:organisation_id>/invite-party-check",
        caseworker_invite.OrganisationInviteReviewView.as_view(),
        name="invite-party-check",
    ),
    path(
        "case/<uuid:case_id>/invite/invite-party-complete",
        caseworker_invite.OrganisationInviteCompleteView.as_view(),
        name="invite-party-complete",
    ),
]

# merge organisations URLS
urlpatterns += [
    path(
        "merge_organisations/review_potential_duplicates_landing/<uuid:invitation_id>/",
        merge_organisations.ReviewPotentialDuplicatesLanding.as_view(),
        name="merge_organisations_review_potential_duplicates_landing",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/exit_merge_process/"
        "<uuid:organisation_merge_record_id>/",
        merge_organisations.ExitMergeOrganisationsView.as_view(),
        name="submission_merge_organisations_exit_merge_process",
    ),
    path(
        "merge_organisations/exit_merge_process/<uuid:organisation_merge_record_id>/",
        merge_organisations.ExitMergeOrganisationsView.as_view(),
        name="merge_organisations_exit_merge_process",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/review_matching_organisations/"
        "<uuid:organisation_merge_record_id>/",
        merge_organisations.ReviewMatchingOrganisationsView.as_view(),
        name="submission_merge_organisations_review_matching_organisations",
    ),
    path(
        "merge_organisations/review_matching_organisations/<uuid:organisation_merge_record_id>/",
        merge_organisations.ReviewMatchingOrganisationsView.as_view(),
        name="merge_organisations_review_matching_organisations",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/select_differences_looper/"
        "<uuid:organisation_merge_record_id>/",
        merge_organisations.SelectDifferencesLooperView.as_view(),
        name="submission_merge_organisations_select_differences_looper",
    ),
    path(
        "merge_organisations/select_differences_looper/" "<uuid:organisation_merge_record_id>/",
        merge_organisations.SelectDifferencesLooperView.as_view(),
        name="merge_organisations_select_differences_looper",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/select_if_duplicate/"
        "<uuid:organisation_merge_record_id>/<uuid:duplicate_organisation_merge_id>/",
        merge_organisations.SelectIfDuplicateView.as_view(),
        name="submission_merge_organisations_select_if_duplicate",
    ),
    path(
        "merge_organisations/select_if_duplicate/<uuid:organisation_merge_record_id>/"
        "<uuid:duplicate_organisation_merge_id>/",
        merge_organisations.SelectIfDuplicateView.as_view(),
        name="merge_organisations_select_if_duplicate",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/confirm_not_duplicate/"
        "<uuid:organisation_merge_record_id>/<uuid:duplicate_organisation_merge_id>/",
        merge_organisations.ConfirmNotDuplicateView.as_view(),
        name="submission_merge_organisations_confirm_not_duplicate",
    ),
    path(
        "merge_organisations/confirm_not_duplicate/<uuid:organisation_merge_record_id>/"
        "<uuid:duplicate_organisation_merge_id>/",
        merge_organisations.ConfirmNotDuplicateView.as_view(),
        name="merge_organisations_confirm_not_duplicate",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/select_differences/"
        "<uuid:organisation_merge_record_id>/<uuid:duplicate_organisation_merge_id>/",
        merge_organisations.SelectDifferencesView.as_view(),
        name="submission_merge_organisations_select_differences",
    ),
    path(
        "merge_organisations/select_differences/<uuid:organisation_merge_record_id>/"
        "<uuid:duplicate_organisation_merge_id>/",
        merge_organisations.SelectDifferencesView.as_view(),
        name="merge_organisations_select_differences",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/choose_correct_case_role/"
        "<uuid:organisation_merge_record_id>/",
        merge_organisations.SelectCorrectCaseRoleView.as_view(),
        name="submission_merge_organisations_choose_correct_case_role",
    ),
    path(
        "merge_organisations/choose_correct_case_role/" "<uuid:organisation_merge_record_id>/",
        merge_organisations.SelectCorrectCaseRoleView.as_view(),
        name="merge_organisations_choose_correct_case_role",
    ),
    path(
        "merge_organisations/choose_correct_case_role/" "<uuid:organisation_merge_record_id>/",
        merge_organisations.SelectCorrectCaseRoleView.as_view(),
        name="merge_organisations_choose_correct_case_role",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/review_merge/"
        "<uuid:organisation_merge_record_id>/",
        merge_organisations.ReviewMergeView.as_view(),
        name="submission_merge_organisations_review",
    ),
    path(
        "merge_organisations/review_merge/<uuid:organisation_merge_record_id>/",
        merge_organisations.ReviewMergeView.as_view(),
        name="merge_organisations_review",
    ),
    path(
        "submission/<uuid:submission_id>/merge_organisations/cancel_merge/"
        "<uuid:organisation_merge_record_id>/",
        merge_organisations.CancelMergeView.as_view(),
        name="submission_cancel_organisation_merge",
    ),
    path(
        "merge_organisations/cancel_merge/<uuid:organisation_merge_record_id>/",
        merge_organisations.CancelMergeView.as_view(),
        name="cancel_organisation_merge",
    ),
    path(
        "submission/merge_organisations/merge_complete/",
        TemplateView.as_view(template_name="v2/merge_organisations/merge_complete.html"),
        name="submission_merge_organisations_merge_complete",
    ),
]


# Adhoc Merge Organisations
urlpatterns += [
    path(
        "adhoc_organisation_merge/start/",
        adhoc_organisation_merge.StartView.as_view(),
        name="adhoc_organisation_merge_start",
    ),
]

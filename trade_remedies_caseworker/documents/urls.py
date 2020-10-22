from django.urls import path

from .views import (
    DocumentsView,
    DocumentStreamDownloadView,
    ApplicationBundleView,
    ApplicationBundleFormView,
    ApplicationBundleDocumentsFormView,
    DocumentSearchView,
)

urlpatterns = [
    path("", DocumentsView.as_view(), name="documents"),
    path(
        "<uuid:document_id>/download/",
        DocumentStreamDownloadView.as_view(),
        name="document",
    ),
    # Search
    path("search/", DocumentSearchView.as_view()),
    # Bundles
    path("bundles/", ApplicationBundleView.as_view(), name="appbundle"),
    path("bundle/create/", ApplicationBundleFormView.as_view(), name="appbundlecreate"),
    path(
        "bundle/<uuid:bundle_id>/",
        ApplicationBundleDocumentsFormView.as_view(),
        name="appbundleedit",
    ),
    path(
        "bundle/<uuid:bundle_id>/remove/document/<uuid:document_id>/",
        ApplicationBundleDocumentsFormView.as_view(),
        name="appbundledeldoc",
    ),
]

from django.urls import path
from .views import UserManagerView, UserView, MyAccountView, ContactLookupView


urlpatterns = [
    path("", UserManagerView.as_view(), name="users"),
    path("my-account/", MyAccountView.as_view(), name="users_my_account"),
    path("contact_lookup/", ContactLookupView.as_view(), name="contact_lookup"),
    path("<uuid:user_id>/delete/", UserView.as_view(delete_user=True), name="delete_user"),
    path("investigator/<uuid:user_id>/", UserView.as_view(), name="edit_investigator"),
    path("cusomter/<uuid:user_id>/", UserView.as_view(), name="edit_customer"),
    path("create/investigator/", UserView.as_view(), name="create_investigator"),
    path("create/customer/", UserView.as_view(), name="create_customer"),
]

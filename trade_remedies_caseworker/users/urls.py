from django.urls import path
from .views import UserManagerView, UserView, MyAccountView, ContactLookupView


urlpatterns = [
    path('', UserManagerView.as_view(), name='users'),
    path('my-account/', MyAccountView.as_view(), name='users_my_account'),
    path('contact_lookup/', ContactLookupView.as_view(), name='contact_lookup'),
    path('<uuid:user_id>/', UserView.as_view(), name='user'),
    path('<uuid:user_id>/delete/', UserView.as_view(delete_user=True), name='user'),
    path('<str:user_group>/<uuid:user_id>/', UserView.as_view(), name='user'),
    path('<str:user_group>/create/', UserView.as_view(), name='user'),
    path('<str:user_group>/', UserManagerView.as_view(), name='users'),
    path('create/<str:user_group>/', UserView.as_view(), name='user'),

]

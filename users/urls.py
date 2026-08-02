# users/urls.py

from django.urls import path
from .views import UserRegistrationView, EmailVerificationView

app_name = "users"

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("verify/<str:token>/", EmailVerificationView.as_view(), name="verify"),
]
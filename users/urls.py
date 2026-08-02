# users/urls.py

from django.urls import path

from .views import (
    EmailVerificationView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    UserRegistrationView,
)

app_name = "users"

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("verify/<str:token>/", EmailVerificationView.as_view(), name="verify"),
    # Сброс пароля.
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset-confirm/<uid>/<token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]

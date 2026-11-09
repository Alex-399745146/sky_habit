from django.urls import path

from .web_views import (
    ProfileView,
    RegisterView,
    ResendVerificationView,
    TelegramGuideView,
    VerifyEmailView,
    WebLoginView,
    WebLogoutView,
)

app_name = "users_web"

urlpatterns = [
    path("login/", WebLoginView.as_view(), name="login"),
    path("logout/", WebLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify/resend/", ResendVerificationView.as_view(), name="resend-verification"),
    path("verify/<str:token>/", VerifyEmailView.as_view(), name="verify"),
    path("guides/telegram/", TelegramGuideView.as_view(), name="telegram-guide"),
    path("profile/", ProfileView.as_view(), name="profile"),
]

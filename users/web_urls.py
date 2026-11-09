from django.urls import path

from .web_views import ProfileView, RegisterView, WebLoginView, WebLogoutView

app_name = "users_web"

urlpatterns = [
    path("login/", WebLoginView.as_view(), name="login"),
    path("logout/", WebLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
]

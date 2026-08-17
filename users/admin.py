# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import EmailAuthenticationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "email", "is_verified", "is_staff", "is_active", "date_joined")
    list_filter = ("is_verified", "is_staff", "is_active")
    search_fields = ("email",)
    readonly_fields = ("date_joined",)

    # Убираем username из формы создания/редактирования пользователя в админке
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {"fields": ("is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_verified", "is_staff", "is_superuser"),
            },
        ),
    )

    # Указываем, что поле username не используется
    ordering = ("email",)

    # Форма авторизации в админке через email
    login_form = EmailAuthenticationForm

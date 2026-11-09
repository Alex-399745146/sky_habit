# users/forms.py

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from config.ui import apply_bootstrap_classes

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """
    Форма аутентификации по email вместо username.
    """

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)


class UserRegistrationForm(forms.ModelForm):
    """Регистрация пользователя в веб-интерфейсе."""

    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Минимум 8 символов, не только цифры.",
    )
    password2 = forms.CharField(
        label="Повторите пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]
        labels = {
            "email": "Email",
            "first_name": "Имя",
            "last_name": "Фамилия",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают.")
        elif password1:
            try:
                password_validation.validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = User.objects.normalize_email(self.cleaned_data["email"])
        user.username = user.email
        user.is_verified = False
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class ProfileForm(forms.ModelForm):
    """Редактирование имени и фамилии в личном кабинете."""

    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)

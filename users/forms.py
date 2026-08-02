# users/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """
    Форма аутентификации по email вместо username.
    """

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )
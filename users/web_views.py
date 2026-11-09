import uuid
from typing import cast

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, View

from telegram_bot.forms import TelegramProfileForm
from telegram_bot.models import TelegramProfile

from .forms import EmailAuthenticationForm, ProfileForm, UserRegistrationForm
from .services import EmailVerificationService


class WebLoginView(LoginView):
    """Вход в веб-интерфейс по email."""

    authentication_form = EmailAuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True


class WebLogoutView(LogoutView):
    """Выход из веб-интерфейса (POST)."""

    next_page = reverse_lazy("home")


class RegisterView(FormView):
    """Регистрация пользователя в веб-интерфейсе."""

    template_name = "users/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        token = str(uuid.uuid4())
        EmailVerificationService.send_verification_email(user.email, token)
        login(self.request, user)
        messages.success(
            self.request,
            "Аккаунт создан. Письмо с подтверждением сохранено в tmp/emails/ (dev-режим).",
        )
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, View):
    """Личный кабинет: имя, статистика и Telegram-профиль."""

    template_name = "users/profile.html"

    def _telegram_profile(self) -> TelegramProfile:
        profile, _ = TelegramProfile.objects.get_or_create(user=self.request.user)
        return cast(TelegramProfile, profile)

    def _context(self, form: ProfileForm, telegram_form: TelegramProfileForm) -> dict:
        user = self.request.user
        return {
            "form": form,
            "telegram_form": telegram_form,
            "habits_count": user.habits.count(),
            "places_count": user.places.count(),
            "public_habits_count": user.habits.filter(is_public=True).count(),
        }

    def get(self, request):
        return render(
            request,
            self.template_name,
            self._context(
                ProfileForm(instance=request.user),
                TelegramProfileForm(instance=self._telegram_profile()),
            ),
        )

    def post(self, request):
        telegram_profile = self._telegram_profile()

        if "save_profile" in request.POST:
            form = ProfileForm(request.POST, instance=request.user)
            telegram_form = TelegramProfileForm(instance=telegram_profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Профиль обновлён.")
                return redirect("users_web:profile")
        elif "save_telegram" in request.POST:
            form = ProfileForm(instance=request.user)
            telegram_form = TelegramProfileForm(request.POST, instance=telegram_profile)
            if telegram_form.is_valid():
                telegram_form.save()
                messages.success(request, "Telegram-профиль сохранён.")
                return redirect("users_web:profile")
        else:
            form = ProfileForm(instance=request.user)
            telegram_form = TelegramProfileForm(instance=telegram_profile)

        return render(request, self.template_name, self._context(form, telegram_form))

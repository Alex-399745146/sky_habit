import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View

from telegram_bot.services import TelegramNotConfigured, send_habit_card

from .forms import HabitForm, PlaceForm
from .models import Habit, Place

logger = logging.getLogger(__name__)

User = get_user_model()


class HomeView(TemplateView):
    """Главная страница с публичной лентой и быстрыми действиями."""

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        public_habits = Habit.objects.filter(is_public=True).select_related("owner", "place")
        context["public_habits"] = public_habits[:6]
        context["public_count"] = public_habits.count()
        context["users_count"] = User.objects.count()
        if self.request.user.is_authenticated:
            context["my_habits_count"] = Habit.objects.filter(owner=self.request.user).count()
            context["my_places_count"] = Place.objects.filter(owner=self.request.user).count()
        return context


class PublicHabitListView(ListView):
    """Публичная лента привычек, доступна без входа."""

    model = Habit
    template_name = "habits/public_habit_list.html"
    context_object_name = "habits"
    paginate_by = 9

    def get_queryset(self):
        return Habit.objects.filter(is_public=True).select_related("owner", "place", "linked_habit")


class HabitListView(LoginRequiredMixin, ListView):
    """Привычки текущего пользователя."""

    model = Habit
    template_name = "habits/habit_list.html"
    context_object_name = "habits"
    paginate_by = 9

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user).select_related("place", "linked_habit")


class HabitDetailView(DetailView):
    """Детальная страница привычки: своя или публичная."""

    model = Habit
    template_name = "habits/habit_detail.html"
    context_object_name = "habit"

    def get_queryset(self):
        queryset = Habit.objects.select_related("owner", "place", "linked_habit")
        if self.request.user.is_authenticated:
            return queryset.filter(Q(is_public=True) | Q(owner=self.request.user))
        return queryset.filter(is_public=True)


class HabitFormMixin:
    """Передаёт пользователя в форму и ограничивает выборку его данными."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class PlaceFormMixin:
    """Передаёт пользователя в форму места."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class HabitCreateView(LoginRequiredMixin, HabitFormMixin, SuccessMessageMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = "habits/habit_form.html"
    success_url = reverse_lazy("habits_web:list")
    success_message = "Привычка «%(action)s» создана."
    extra_context = {"title": "Новая привычка", "submit_label": "Создать"}

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class HabitUpdateView(LoginRequiredMixin, HabitFormMixin, SuccessMessageMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = "habits/habit_form.html"
    success_url = reverse_lazy("habits_web:list")
    success_message = "Привычка «%(action)s» обновлена."
    extra_context = {"title": "Редактировать привычку", "submit_label": "Сохранить"}

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)


class HabitDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Habit
    template_name = "habits/habit_confirm_delete.html"
    success_url = reverse_lazy("habits_web:list")
    success_message = "Привычка «%(action)s» удалена."

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)


class PlaceListView(LoginRequiredMixin, ListView):
    """Места текущего пользователя."""

    model = Place
    template_name = "habits/place_list.html"
    context_object_name = "places"
    paginate_by = 12

    def get_queryset(self):
        return (
            Place.objects.filter(owner=self.request.user)
            .annotate(habits_count=Count("habits"))
            .order_by("-created_at")
        )


class PlaceCreateView(LoginRequiredMixin, PlaceFormMixin, SuccessMessageMixin, CreateView):
    model = Place
    form_class = PlaceForm
    template_name = "habits/place_form.html"
    success_url = reverse_lazy("habits_web:place-list")
    success_message = "Место «%(name)s» создано."
    extra_context = {"title": "Новое место", "submit_label": "Создать"}

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PlaceUpdateView(LoginRequiredMixin, PlaceFormMixin, SuccessMessageMixin, UpdateView):
    model = Place
    form_class = PlaceForm
    template_name = "habits/place_form.html"
    success_url = reverse_lazy("habits_web:place-list")
    success_message = "Место «%(name)s» обновлено."
    extra_context = {"title": "Редактировать место", "submit_label": "Сохранить"}

    def get_queryset(self):
        return Place.objects.filter(owner=self.request.user)


class PlaceDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Place
    template_name = "habits/place_confirm_delete.html"
    success_url = reverse_lazy("habits_web:place-list")
    success_message = "Место «%(name)s» удалено."

    def get_queryset(self):
        return Place.objects.filter(owner=self.request.user)


class SendHabitCardView(LoginRequiredMixin, View):
    """Принудительно отправляет карточку привычки в Telegram."""

    def post(self, request, pk):
        habit = get_object_or_404(
            Habit.objects.select_related("owner", "place", "linked_habit"),
            pk=pk,
            owner=request.user,
        )

        try:
            send_habit_card(habit)
        except TelegramNotConfigured:
            messages.error(request, "Telegram не привязан. Укажите chat ID в профиле.")
        except Exception:
            logger.exception("Не удалось отправить карточку привычки %s", habit.pk)
            messages.error(request, "Не удалось отправить карточку. Проверьте токен бота и chat ID.")
        else:
            messages.success(request, f"Карточка «{habit.action}» отправлена в Telegram.")

        return redirect("habits_web:detail", pk=habit.pk)


class SendAllHabitCardsView(LoginRequiredMixin, View):
    """Принудительно отправляет все карточки привычек в Telegram."""

    def post(self, request):
        profile = getattr(request.user, "telegram_profile", None)
        if profile is None or not profile.telegram_chat_id:
            messages.error(request, "Telegram не привязан. Укажите chat ID в профиле.")
            return redirect("users_web:profile")

        habits = list(
            Habit.objects.filter(owner=request.user).select_related("place", "linked_habit"),
        )
        if not habits:
            messages.info(request, "У вас пока нет привычек.")
            return redirect("users_web:profile")

        sent = 0
        failed = 0
        for habit in habits:
            try:
                send_habit_card(habit)
            except Exception:
                logger.exception("Не удалось отправить карточку привычки %s", habit.pk)
                failed += 1
            else:
                sent += 1

        if sent:
            messages.success(request, f"Отправлено карточек: {sent}.")
        if failed:
            messages.warning(request, f"Не удалось отправить: {failed}.")

        return redirect("users_web:profile")

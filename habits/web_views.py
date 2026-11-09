from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import HabitForm, PlaceForm
from .models import Habit, Place

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

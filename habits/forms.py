from django import forms
from django.core.exceptions import ValidationError

from config.ui import apply_bootstrap_classes

from .models import Habit, Place


class PlaceForm(forms.ModelForm):
    """Создание и редактирование места."""

    class Meta:
        model = Place
        fields = ["name", "description", "is_public"]
        labels = {
            "name": "Название",
            "description": "Описание",
            "is_public": "Публичное место",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and not self.instance.pk:
            self.instance.owner = user
        apply_bootstrap_classes(self)

    def clean_name(self):
        name = self.cleaned_data["name"]
        duplicates = Place.objects.filter(owner=self.user, name=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError("Место с таким названием уже есть.")
        return name


class HabitForm(forms.ModelForm):
    """Создание и редактирование привычки."""

    class Meta:
        model = Habit
        fields = [
            "action",
            "place",
            "time",
            "is_pleasant",
            "linked_habit",
            "reward",
            "frequency",
            "time_to_complete",
            "is_public",
        ]
        labels = {
            "action": "Действие",
            "place": "Место",
            "time": "Время",
            "is_pleasant": "Приятная привычка",
            "linked_habit": "Связанная привычка",
            "reward": "Вознаграждение",
            "frequency": "Периодичность, дней",
            "time_to_complete": "Время на выполнение, сек",
            "is_public": "Публичная привычка",
        }
        widgets = {
            "action": forms.TextInput(attrs={"placeholder": "Например: сделать зарядку"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "reward": forms.TextInput(attrs={"placeholder": "Например: чашка кофе"}),
            "frequency": forms.NumberInput(attrs={"min": 1, "max": 7}),
            "time_to_complete": forms.NumberInput(attrs={"min": 1, "max": 120}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["place"].queryset = Place.objects.filter(owner=user)
            linked_habits = Habit.objects.filter(owner=user, is_pleasant=True)
            if self.instance.pk:
                linked_habits = linked_habits.exclude(pk=self.instance.pk)
            self.fields["linked_habit"].queryset = linked_habits

        self.fields["place"].empty_label = "Без места"
        self.fields["linked_habit"].empty_label = "Без связанной привычки"
        apply_bootstrap_classes(self)

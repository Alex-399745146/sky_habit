# habits/serializers.py

from rest_framework import serializers

from .models import Habit, Place


class PlaceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Place.
    """

    class Meta:
        model = Place
        fields = ["id", "owner", "name", "description", "is_public", "created_at"]
        read_only_fields = ["owner", "created_at"]


class HabitSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Habit.
    Валидация бизнес-правил:
    - нельзя одновременно reward и linked_habit;
    - у приятной привычки не может быть reward или linked_habit;
    - linked_habit должна быть приятной привычкой.
    """

    class Meta:
        model = Habit
        fields = [
            "id",
            "owner",
            "place",
            "time",
            "action",
            "is_pleasant",
            "linked_habit",
            "reward",
            "frequency",
            "time_to_complete",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def validate(self, attrs):
        """
        Валидация бизнес-правил на уровне сериализатора.
        """
        reward = attrs.get("reward")
        linked_habit = attrs.get("linked_habit")
        is_pleasant = attrs.get("is_pleasant", False)

        # 1. Нельзя одновременно reward и linked_habit
        if reward and linked_habit:
            raise serializers.ValidationError("Нельзя одновременно указать вознаграждение и связанную привычку.")

        # 2. У приятной привычки не может быть reward или linked_habit
        if is_pleasant:
            if reward:
                raise serializers.ValidationError("У приятной привычки не может быть вознаграждения.")
            if linked_habit:
                raise serializers.ValidationError("У приятной привычки не может быть связанной привычки.")

        # 3. linked_habit должна указывать только на приятную привычку
        if linked_habit and not linked_habit.is_pleasant:
            raise serializers.ValidationError("Связанная привычка должна быть приятной.")

        return attrs

# habits/views.py

from rest_framework import generics, permissions

from .models import Habit, Place
from .pagination import HabitPagination
from .permissions import IsOwnerOrReadOnlyForPlace, IsOwnerReadWrite
from .serializers import HabitSerializer, PlaceSerializer


class PlaceListCreateView(generics.ListCreateAPIView):
    """
    Список мест текущего пользователя + создание нового места.
    """

    serializer_class = PlaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Place.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PlaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Просмотр, редактирование, удаление конкретного места (только владелец).
    """

    serializer_class = PlaceSerializer
    permission_classes = [IsOwnerReadWrite]

    def get_queryset(self):
        return Place.objects.filter(owner=self.request.user)


class HabitListCreateView(generics.ListCreateAPIView):
    """
    Список привычек текущего пользователя + создание новой привычки.
    Пагинация: 5 привычек на страницу.
    """

    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class HabitDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Просмотр, редактирование, удаление конкретной привычки (только владелец).
    """

    serializer_class = HabitSerializer
    permission_classes = [IsOwnerReadWrite]

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    """
    Список публичных привычек (доступно всем, только чтение).
    Пагинация: 5 привычек на страницу.
    """

    serializer_class = HabitSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = HabitPagination

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)

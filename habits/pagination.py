# habits/pagination.py

from rest_framework.pagination import LimitOffsetPagination


class HabitPagination(LimitOffsetPagination):
    """
    Пагинация для привычек: 5 привычек на страницу по умолчанию.
    """

    default_limit = 5
    max_limit = 50

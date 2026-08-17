# habits/permissions.py

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает:
    - чтение любому пользователю (для публичных объектов);
    - редактирование/удаление только владельцу.
    """

    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем (для публичных привычек это будет использоваться отдельно)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Изменение/удаление — только владельцу
        return obj.owner == request.user


class IsOwnerOrReadOnlyForPlace(permissions.BasePermission):
    """
    Разрешает:
    - чтение только если объект публичный ИЛИ владелец;
    - редактирование/удаление только владельцу.
    """

    def has_object_permission(self, request, view, obj):
        # Чтение
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.owner == request.user

        # Изменение/удаление — только владельцу
        return obj.owner == request.user


class IsOwnerReadWrite(permissions.BasePermission):
    """
    Разрешает полный доступ только владельцу объекта.
    Для привычек и мест, которые не публичные.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

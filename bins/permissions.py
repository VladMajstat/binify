from rest_framework.permissions import BasePermission


class IsAuthor(BasePermission):
    """Лише аутентифікований автор об'єкта."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsAuthorOrAdmin(BasePermission):
    """Аутентифікований користувач, якщо він автор або адмін."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user.is_staff


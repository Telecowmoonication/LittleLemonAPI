from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_superuser
        )
        

class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        is_employee = request.user.groups.filter(name='Employee').exists()
        is_manager = request.user.groups.filter(name='Manager').exists()
        return bool(
            request.user and request.user.is_authenticated and
            (is_employee or is_manager or request.user.is_superuser)
        )
        

class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        is_manager = request.user.groups.filter(name='Manager').exists()
        return bool(
            request.user and request.user.is_authenticated and
            (is_manager or request.user.is_superuser)
        )


class IsAdminOrManagerOrEmployee(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            is_employee = request.user.groups.filter(name='Employee').exists()
            is_manager = request.user.groups.filter(name='Manager').exists()
            return bool(is_employee or is_manager or request.user.is_superuser)
        return False
    

class IsOwnerOrAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        is_manager = request.user.groups.filter(name='Manager').exists()
        return bool(obj.first_name == request.user.first_name and
                    obj.last_name == request.user.last_name or
                    is_manager or request.user.is_superuser)
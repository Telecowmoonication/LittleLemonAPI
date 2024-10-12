from rest_framework.permissions import BasePermission


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        is_employee = request.user.groups.filter(name='Employee').exists()
        is_manager = request.user.groups.filter(name='Manager').exists()
        is_delivery_crew = request.user.groups.filter(name='Delivery Crew').exists()
        return bool(
            request.user and request.user.is_authenticated and
            (is_employee or is_delivery_crew or is_manager or request.user.is_superuser)
        )
        

class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        is_manager = request.user.groups.filter(name='Manager').exists()
        return bool(
            request.user and request.user.is_authenticated and
            (is_manager or request.user.is_superuser)
        )
    

class IsOwnerOrAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        is_manager = request.user.groups.filter(name='Manager').exists()
        return bool(obj.first_name == request.user.first_name and
                    obj.last_name == request.user.last_name or
                    is_manager or request.user.is_superuser)
        
        
class IsOwnerOrEmployeeOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        is_employee = request.user.groups.filter(name='Employee').exists()
        return bool(obj.first_name == request.user.first_name and
                    obj.last_name == request.user.last_name or
                    is_employee or request.user.is_superuser)
        
        
class IsEmployeeOrAssignedDeliveryCrewOrCustomerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True
        if user.groups.filter(name='Employee').exists():
            return True
        if user.groups.filter(name='Delivery Crew').exists():
            return True
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        if user.groups.filter(name='Employee').exists():
            return True
        if user.groups.filter(name='Delivery Crew').exists():
            return obj.delivery_crew == user
        return obj.user == user
    
    
class IsAdminOrEmployeeButNotDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                return True
            if user.groups.filter(name='Employee').exists() and not user.groups.filter(name='Delivery Crew').exists():
                return True
        return False
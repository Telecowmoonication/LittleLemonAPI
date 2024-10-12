from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Logger, UserComments, Category, MenuItem, Booking, Cart, Order, OrderItem

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Display specific fields in the list view in the admin
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']

    # Fields that will be searchable in the admin
    search_fields = ['username', 'email', 'first_name', 'last_name']

    # Filters for the list view in the admin
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']


admin.site.register(Logger)
admin.site.register(UserComments)
admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Booking)
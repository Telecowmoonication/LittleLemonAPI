from django.contrib import admin
from .models import Logger, UserComments, Category, MenuItem, Booking, Cart, Order, OrderItem

# Register your models here.
admin.site.register(Logger)
admin.site.register(UserComments)
admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(Booking)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
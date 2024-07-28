from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register', views.user_registration, name='register'), # API view to create new user
    path('api-token-auth', obtain_auth_token, name='api-token-auth'), # User can log in to generate auth tokens (API)
    path('accounts/login', auth_views.LoginView.as_view(), name='login'), # Django's built-in login view (HTML)
    path('', views.index, name='index'), # Home page (HTML)
    path('api/logger', views.logger_api_view, name='logger_api_view'), # API view for employees to log/view hours
    path('logger', views.logger_view, name='logger_view'), # AJAX view for employees to log/view hours
    path('api/search', views.search_api_view, name='search_api_view'), # API view to search MenuItems and Categories
    path('search', views.search_view, name='search_view'), # HTML view to search MenuItems and Categories
    path('api/comments', views.comments_api_view, name='comments_api_view'), # API view for comments about restaurant
    path('comments', views.comments_view, name='comments_view'), # HTML view for comments about restaurant
    path('api/groups/employee/users', views.employee_api_view, name='employee_api_view'), # API view to display/add users to Employee group
    path('groups/employee/users', views.employee_view, name='employee_view'), # HTML view to display/add users to Employee group
    path('api/groups/employee/users/<str:username>', views.employee_delete_api_view, name='employee_delete_api_view'), # API view to remove users from Employee group
    path('groups/employee/users/<str:username>', views.employee_delete_view, name='employee_delete_view'), # HTML view to remove users from Employee group
    path('api/groups/manager/users', views.manager_api_view, name='manager_api_view'), # API view to display/add users to Manager group
    path('groups/manager/users', views.manager_view, name='manager_view'), # HTML view to display/add users to Manager group
    path('api/groups/manager/users/<str:username>', views.manager_delete_api_view, name='manager_delete_api_view'), # API view to remove users from Manager group
    path('groups/manager/users/<str:username>', views.manager_delete_view, name='manager_delete_view'), # HTML view to remove users from Manager group
    path('api/groups/delivery-crew/users', views.delivery_crew_api_view, name='delivery_crew_api_view'), # API view to display/add users to Delivery Crew group
    path('groups/delivery-crew/users', views.delivery_crew_view, name='delivery_crew_view'), # HTML view to display/add users to Delivery Crew group
    path('api/groups/delivery-crew/users/<str:username>', views.delivery_crew_delete_api_view, name='delivery_crew_delete_api_view'), # API view to remove users from Delivery Crew group
    path('groups/delivery-crew/users/<str:username>', views.delivery_crew_delete_view, name='delivery_crew_delete_view'), # HTML view to remove users from Delivery Crew group
    path('api/category', views.category_api_view, name='category_api_view'), # API view to display/add categories
    path('category', views.category_view, name='category_view'), # HTML view to display/add categories
    path('api/category/delete/<slug:slug>', views.category_delete_api_view, name='category_delete_api_view'), # API view to delete categories
    path('category/delete/<slug:slug>', views.category_delete_view, name='category_delete_view'), # HTML view to delete categories
    path('api/category/<slug:category_slug>', views.category_details_api_view, name='category_details_api_view'), # API view to display menu items in category
    path('category/<slug:category_slug>', views.category_details_view, name='category_details_view'), # HTML view to display menu items in category
    path('api/menu', views.menu_api_view, name='menu_api_view'), # API view to display menu/add menu items
    path('menu', views.menu_view, name='menu_view'), # HTML view to display menu/add menu items
    path('api/menu-item/<slug:slug>', views.menu_item_api_view, name='menu_item_api_view'), # API view to display individual menu items
    path('menu-item/<slug:slug>', views.menu_item_view, name='menu_item_view'), # HTML view to display individual menu items
    path('api/menu-item/delete/<slug:slug>', views.menu_item_delete_api_view, name='menu_item_delete_api_view'), # API view to delete menu items
    path('menu-item/delete/<slug:slug>', views.menu_item_delete_view, name='menu_item_delete_view'), # HTML view to delete menu items
    path('api/cart', views.cart_api_view, name='cart_api_view'), # API view to display, add, delete items in user cart
    path('cart', views.cart_view, name='cart_view'), # HTML view to display, update, delete items in user cart
    path('api/orders', views.orders_api_view, name='orders_api_view'), # API view to display and create orders
    path('orders', views.orders_view, name='orders_view'), # HTML view to display and create orders
    path('api/orders/<int:order_id>', views.order_details_api_view, name='order_details_api_view'), # API view to display, update, and delete orders
    path('orders/<int:order_id>', views.order_details_view, name='order_details_view'), # HTML view to display, update, and delete orders
    path('api/booking', views.booking_api_view, name='booking_api_view'), # API view for users to book a reservation
    path('booking', views.booking_view, name='booking_view'), # HTML view for users to book a reservation
    path('api/reservations', views.reservations_api_view, name='reservations_api_view'), # API view to display current reservations
    path('reservations', views.reservations_view, name='reservations_view'), # HTML view to display current reservations
    path('api/reservations/old', views.old_reservations_api_view, name='old_reservations_api_view'), # API view to display past reservations
    path('reservations/old', views.old_reservations_view, name='old_reservations_view'), # HTML view to display past reservations
    path('api/reservations/<int:reservation_id>', views.reservation_details_api_view, name='reservation_details_api_view'), # API view to display reservation details, update, and delete reservations
    path('reservations/<int:reservation_id>', views.reservation_details_view, name='reservation_details_view'), # HTML view to display reservation details, update, and delete reservations
]
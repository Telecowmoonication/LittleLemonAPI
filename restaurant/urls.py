from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register', views.user_registration, name='register'), # API view to create new user
    path('api-token-auth', obtain_auth_token, name='api-token-auth'), # User can log in to generate auth tokens (API)
    path('accounts/login', auth_views.LoginView.as_view(), name='login'), # Django's built-in login view (HTML)
    path('', views.index, name='index'), # Home page (HTML)
    path('logger', views.logger_view, name='logger_view'), # AJAX view for employees to log/view hours
    path('api/logger', views.logger_api_view, name='logger_api_view'), # API view for employees to log/view hours
    path('search', views.search_view, name='search_view'), # HTML view to search MenuItems and Categories 
    path('api/search', views.search_api_view, name='search_api_view'), # API view to search MenuItems and Categories
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
    
]
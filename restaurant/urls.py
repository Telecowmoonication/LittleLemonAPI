from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register', views.user_registration, name='register'), # Create new user
    path('api-token-auth', obtain_auth_token, name='api-token-auth'), # User can log in and generate auth tokens
    path('logger', views.logger_view, name='logger_view'), # AJAX view for employees to log/view hours
    path('api/logger', views.logger_api_view, name='logger_api_view'), # API view for employees to log/view hours
    path('search', views.search_view, name='search_view'), # HTML view to search MenuItems and Categories 
    path('api/search', views.search_api_view, name='search_api_view'), # API view to search MenuItems and Categories 
    
]
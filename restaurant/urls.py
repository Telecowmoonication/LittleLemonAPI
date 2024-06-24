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
    
]
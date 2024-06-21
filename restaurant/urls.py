from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('search', views.search_view, name='search_view'),
    path('api/search', views.search_api_view, name='search_api_view'),
]
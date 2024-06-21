from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.forms import ValidationError  # Might not need
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import User, Group
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes, throttle_classes
from rest_framework.renderers import TemplateHTMLRenderer, StaticHTMLRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication # Might not need
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status, viewsets, generics
from decimal import Decimal
from .models import MenuItem, Category, Cart, Order, OrderItem, UserComments
# from .forms import LogForm, CommentForm
# from .permissions import IsAdminOrManager, IsAdmin
from .serializers import UserSerializer, UserRegSerializer, LoggerSerializer, UserCommentsSerializer, CategorySerializer, MenuItemSerializer, BookingSerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from datetime import datetime

# Create your views here.



# Allows all users to search for titles from MenuItem and Category
    # GET: Displays search results, 200
# Endpoint: /restaurant/search
# View Type: HTML, AJAX
def search_view(request):
    return render(request, 'flexbox1_search.html')


# Allows all users to search for titles from MenuItem and Category
    # GET: Displays search results, 200
# Endpoint: /restaurant/api/search
# View Type: Function Based, api
@api_view(['GET'])
def search_api_view(request):
    query = request.GET.get('search')
    menuitem_results = MenuItem.objects.filter(title__icontains=query) if query else []
    category_results = Category.objects.filter(title__icontains=query) if query else []
    
    menuitem_serializer = MenuItemSerializer(menuitem_results, many=True)
    category_serializer = CategorySerializer(category_results, many=True)
    
    return Response({
        'menu_items': menuitem_serializer.data,
        'categories': category_serializer.data
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.forms import ValidationError  # Might not need
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes, throttle_classes
from rest_framework.renderers import TemplateHTMLRenderer, StaticHTMLRenderer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication # Might not need
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status, viewsets, generics
from decimal import Decimal
from .models import Logger, UserComments, MenuItem, Category, Cart, Order, OrderItem
from .forms import LogForm, CommentForm
from .permissions import IsAdmin, IsEmployee, IsAdminOrManager, IsAdminOrManagerOrEmployee, IsOwnerOrAdminOrManager
from .serializers import UserSerializer, UserRegSerializer, LoggerSerializer, UserCommentsSerializer, CategorySerializer, MenuItemSerializer, BookingSerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from datetime import datetime

# Create your views here.

# User registration
    # POST: Must submit valid username, email, password, password verification. Creates new user (201)
# Grading criteria 11. Customer can register
# Endpoint: /restaurant/register
# View type: Function based, api
@api_view(['POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def user_registration(request):
    serializer = UserRegSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# To obtain access token, users send a POST request to '/api/api-auth-token' with their username and password
# Response will contain token they can use for authentication
# Include token in Authorization header of any requests that require authentication
# Grading Criteria 12. Customers can log in using their username and password and get access tokens


# Staff log
# Allows employees to log/check their shift hours/hours worked
    # GET: Admin and managers can view all logs, employees can only view their own logs
    # POST: Must submit valid first name, last name, and time. Creates a time log
# Endpoint: /restaurant/logger
# View type: Function based, HTML
@login_required
@permission_classes([IsEmployee])
@throttle_classes([UserRateThrottle])
def logger_view(request):
    if request.method == 'POST':
        form = LogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('logger_view') # Redirect to the same view to clear the form after submission
        
    else:
        form = LogForm()
        
    # Display logged hours
    if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
        logs = Logger.objects.all()
    else:
        logs = Logger.objects.filter(first_name=request.user.first_name, last_name=request.user.last_name)
        
    context = {
        'form': form,
        'logs': logs
    }
    return render(request, 'logger.html', context)


# Staff log API
# Allows employees to log/check their shift hours/hours worked
    # GET: Admin and managers can view all logs, employees can only view their own logs (200)
    # POST: Must submit valid first name, last name, and time. Creates a time log (201)
# Endpoint: /restaurant/api/logger
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrManagerOrEmployee])
@throttle_classes([UserRateThrottle])
def logger_api_view(request):
    if request.method == 'POST':
        serializer = LoggerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Log entry created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            logs = Logger.objects.all()
        else:
            logs = Logger.objects.filter(first_name=request.user.first_name, last_name=request.user.last_name)
        serializer = LoggerSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Home Page
    # GET: Displays the homepage
# Endpoint: /restaurant/index
# View Type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def index(request):
    current_year = datetime.now().year
    return render(request, 'index.html', {'current_year': current_year})


# Search
# Allows all users to search for titles from MenuItem and Category
    # GET: Displays search results (200)
# Endpoint: /restaurant/search
# View Type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
@require_GET
def search_view(request):
    query = request.GET.get('search', '')
    menu_items = MenuItem.objects.filter(title__icontains=query) if query else []
    categories = Category.objects.filter(title__icontains=query) if query else []
    
    context = {
        'query': query,
        'menu_items': menu_items,
        'categories': categories,
    }
    
    return render(request, 'search_results.html', context)


# Search API
# Allows all users to search for titles from MenuItem and Category
    # GET: Displays search results (200)
# Endpoint: /restaurant/api/search
# View Type: Function based, api
@api_view(['GET'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def search_api_view(request):
    query = request.GET.get('search')
    
    if not query:
        return Response({"detail": "Search query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    menuitem_results = MenuItem.objects.filter(title__icontains=query)
    category_results = Category.objects.filter(title__icontains=query)
    
    menuitem_serializer = MenuItemSerializer(menuitem_results, many=True)
    category_serializer = CategorySerializer(category_results, many=True)
    
    return Response({
        'menu_items': menuitem_serializer.data,
        'categories': category_serializer.data
    }, status=status.HTTP_200_OK)
    

# User comments API
# Allows anyone to view comments/reviews about the restaurant
    # GET: Displays previously posted comments
# Allows users to make comments/reviews about the restaurant
    # POST: Submits user comment/review
# Endpoint: /restaurant/api/comments
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def comments_api_view(request):
    if request.method == 'GET':
        comments = UserComments.objects.all()
        serializer = UserCommentsSerializer(comments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = UserCommentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
# User comments
# Allows anyone to view comments/reviews about the restaurant
    # GET: Displays previously posted comments
# Allows users to make comments/reviews about the restaurant, redirects to login for anon
    # POST: Submits user comment/review
# Endpoint: /restaurant/comments
# View type: Function based, HTML, uses comments_api_view to fetch and display data
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def comments_view(request):
    form = CommentForm()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL) # Redirects to login for unauthorized useers trying to POST
        form = CommentForm(request.POST)
        if form.is_valid():
            response = request.post(
                request.build_absolute_uri('/restaurant/comments'),
                data = form.cleaned_data,
                headers = {'Authorization': f'Token {request.user.auth_token.key}'}
            )
            if response.status_code == 201:
                return redirect('comments_view')
            else:
                form.add_error(None, 'Error submitting comment.')
    response = request.get(request.build_absolute_uri('/restaurant/comments'))
    comments = response.json() if response.status_code == 200 else []
    
    context = {
        'form': form,
        'comments': comments
    }
    return render(request, 'comments.html', context)
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.forms import ValidationError  # Might not need
from django.conf import settings
from django.contrib import messages # For better user feedback
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils.text import slugify
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes, throttle_classes
from rest_framework.renderers import TemplateHTMLRenderer, StaticHTMLRenderer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication # Might not need
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status, viewsets, generics
from decimal import Decimal
from .models import Logger, UserComments, MenuItem, Category, Cart, Order, OrderItem
from .forms import LogForm, CommentForm, EmployeeForm, ManagerForm, DeliveryCrewForm, CategoryForm, MenuItemForm, MenuItemDeleteForm, CartForm
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
@permission_classes([AllowAny])
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


# Staff log API
# Allows employees to log/check their shift hours/hours worked
    # GET: Admin and managers can view all logs, employees can only view their own logs (200)
    # POST: Must submit valid first name, last name, and time. Creates a time log (201)
# Endpoint: /restaurant/api/logger
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrManagerOrEmployee])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
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


# Staff log
# Allows employees to log/check their shift hours/hours worked
    # GET: Admin and managers can view all logs, employees can only view their own logs
    # POST: Must submit valid first name, last name, and time. Creates a time log
# Endpoint: /restaurant/logger
# View type: Function based, HTML
@login_required
@permission_classes([IsEmployee])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
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


# Home Page
    # GET: Displays the homepage
# Endpoint: /restaurant/index
# View Type: Function based, HTML
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def index(request):
    current_year = datetime.now().year
    return render(request, 'index.html', {'current_year': current_year})


# Search API
# Allows all users to search for titles from MenuItem and Category
    # GET: Displays search results, 200
# Endpoint: /restaurant/api/search
# View Type: Function based, api
@api_view(['GET'])
@permission_classes([AllowAny])
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
    

# Search
# Allows all users to search for titles from MenuItem and Category
    # GET: Displays search results (200)
# Endpoint: /restaurant/search
# View Type: Function based, HTML
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
                messages.error(request, "Error submitting comment.")
                
    response = request.get(request.build_absolute_uri('/restaurant/comments'))
    comments = response.json() if response.status_code == 200 else []
    
    context = {
        'form': form,
        'comments': comments
    }
    return render(request, 'comments.html', context)


# Allows admin and managers to view and add users to Employee group
    # GET: Displays users in Employee group, 200
    # POST: Assigns user to the Employee group, 201
# Endpoint: /api/groups/employee/users
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def employee_api_view(request):
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        return Response({"message": "Employee group not found."}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        employees = employee_group.user_set.all()
        usernames = [user.username for user in employees]
        return Response(usernames, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            if user in employee_group.user_set.all():
                return Response({"message": f"User {username} is already an employee."}, status=status.HTTP_400_BAD_REQUEST)
            employee_group.user_set.add(user)
            return Response({"message": f"User {username} added to Employee group."}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
# Allows admin and managers to view and add users to Employee group
    # GET: Displays users in Employee group
    # POST: Assigns user to the Employee group
# Endpoint: /groups/employee/users
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def employee_view(request):
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        # Add redirect?
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in employee_group.user_set.all():
                    messages.info(request, f"User {username} is already an employee.")
                else:
                    employee_group.user_set.add(user)
                    messages.success(request, f"User {username} added to Employee Group.")
                return redirect('employee_view')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = EmployeeForm()
        
    employees = employee_group.user_set.all()
    context = {'employees': employees, 'form': form}
    return render(request, 'employee_view.html', context)
                
    
# Allows admin or managers to delete users from the Employee group
    # DELETE: Removes user from group, 200
# Endpoint: /api/groups/employee/users/<str:username>
# View type: Function based, api
@api_view(['DELETE'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def employee_delete_api_view(request, username):
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        return Response({"message": "Employee group not found."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        user = User.objects.get(username=username)
        if user in employee_group.user_set.all():
            employee_group.user_set.remove(user)
            return Response({"message": f"User {username} removed from Employee group."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": f"User {username} not in Employee group."}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# Allows admin or managers to delete users from the Employee group
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /groups/employee/users/<str:username>
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def employee_delete_view(request):
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        # Add redirect?
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in employee_group.user_set.all():
                    employee_group.user_set.remove(user)
                    messages.success(request, f"User {username} removed from Employee group.")
                else:
                    messages.info(request, f"User {username} is not in Employee group.")
                return redirect('employee_delete_view')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = EmployeeForm()
        
    employees = employee_group.user_set.all()
    context = {'employees': employees, 'form': form}
    return render(request, 'employee_delete_view.html', context)


# Allows admin and managers to view and add users to Manager group if they are an employee already
    # GET: Displays users in Manager group, 200
    # POST: Assigns user to the Manager group, 201
# Endpoint: /api/groups/manager/users
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def manager_api_view(request):
    try:
        manager_group = Group.objects.get(name='Manager')
    except Group.DoesNotExist:
        return Response({"message": "Manager group not found."}, status=status.HTTP_404_NOT_FOUND)
        # Add redirect
    
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        return Response({"message": "Employee group not found."}, status=status.HTTP_404_NOT_FOUND)
        # Add redirect
    
    if request.method == 'GET':
        managers = manager_group.user_set.all()
        usernames = [user.username for user in managers]
        return Response(usernames, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            if user in manager_group.user_set.all():
                return Response({"message": f"User {username} is already a manager."}, status=status.HTTP_400_BAD_REQUEST)
            if user not in employee_group.user_set.all():
                return Response({"message": f"User {username} must be an employee first."}, status=status.HTTP_400_BAD_REQUEST)
            manager_group.user_set.add(user)
            return Response({"message": f"User {username} added to Manager group."}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
       
# Allows admin and managers to view and add users to Manager group
    # GET: Displays users in Manager group
    # POST: Assigns user to the Manager group
# Endpoint: /groups/manager/users
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def manager_view(request):
    try:
        manager_group = Group.objects.get(name='Manager')
    except Group.DoesNotExist:
        messages.error(request, "Manager group not found.")
        # Add redirect
        
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        # Add redirect
    
    if request.method == 'POST':
        form = ManagerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in manager_group.user_set.all():
                    messages.info(request, f"User {username} is already a manager.")
                elif user not in employee_group.user_set.all():
                    messages.error(request, f"User {username} must be an employee first.")
                else:
                    manager_group.user_set.add(user)
                    messages.success(request, f"User {username} added to Manager group.")
                return redirect('manager_view')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = ManagerForm()
        
    managers = manager_group.user_set.all()
    context = {'managers': managers, 'form': form}
    return render(request, 'manager_view.html', context)
        

# Allows admin or managers to delete users from the Manager group
    # DELETE: Removes user from group, 200
# Endpoint: /api/groups/manager/users/<str:username>
# View type: Function based, api
@api_view(['DELETE'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def manager_delete_api_view(request, username):
    try:
        manager_group = Group.objects.get(name='Manager')
    except Group.DoesNotExist:
        return Response({"message": "Manager group not found."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        user = User.objects.get(username=username)
        if user in manager_group.user_set.all():
            manager_group.user_set.remove(user)
            return Response({"message": f"User {username} removed from Manager group. User {username} is still in the Employee group."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": f"User {username} is not in Manager group."}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    

# Allows admin or managers to delete users from the Manager group
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /groups/manager/users/<str:username>
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def manager_delete_view(request):
    try:
        manager_group = Group.objects.get(name='Manager')
    except Group.DoesNotExist:
        messages.error(request, "Manager group not found.")
        # Add redirect?
    
    if request.method == 'POST':
        form = ManagerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in manager_group.user_set.all():
                    manager_group.user_set.remove(user)
                    messages.success(request, f"User {username} removed from Manager group. User {username} is still in the Employee group.")
                else:
                    messages.info(request, f"User {username} is not in Manager group.")
                return redirect('manager_delete_view')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = ManagerForm()
        
    managers = manager_group.user_set.all()
    context = {'managers': managers, 'form': form}
    return render(request, 'manager_delete_view.html', context)


# Allows employees to view users in the Delivery Crew group
    # GET: Displays users in Delivery Crew group
# Allows admin and managers to add users to the Delivery Crew group
    # POST: Assigns user to Delivery Crew Group
# Endpoint: /api/groups/delivery-crew/users
# view type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrManagerOrEmployee])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def delivery_crew_api_view(request):
    try:
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
    except Group.DoesNotExist:
        return Response({"message": "Delivery Crew Group not found."}, status=status.HTTP_404_NOT_FOUND)
        # Add redirect
    
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        return Response({"message": "Employee group not found."}, status=status.HTTP_404_NOT_FOUND)
        # Add redirect
    
    if request.method == 'GET':
        drivers = delivery_crew_group.user_set.all()
        usernames = [user.username for user in drivers]
        return Response(usernames, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            username = request.data.get('username')
            if not username:
                return Response({"message": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = User.objects.get(username=username)
                if user in delivery_crew_group.user_set.all():
                    return Response({"message": f"User {username} is already in Delivery Crew group."}, status=status.HTTP_400_BAD_REQUEST)
                if not user in employee_group.user_set.all():
                    return Response({"message": f"User {username} must be an employee first"}, status=status.HTTP_400_BAD_REQUEST)
                delivery_crew_group.user_set.add(user)
                return Response({"message": f"User {username} added to Delivery Crew group."}, status=status.HTTP_201_CREATED)
            except user.DoesNotExist:
                return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Only managers and admins can add users to the Delivery Crew group."}, status=status.HTTP_403_FORBIDDEN)
            

# Allows employees to view users in the Delivery Crew group
    # GET: Displays users in Delivery Crew group
# Allows admin and managers to add users to the Delivery Crew group
    # POST: Assigns user to Delivery Crew Group
# Endpoint: /groups/delivery-crew/users
# view type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManagerOrEmployee])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def delivery_crew_view(request):
    try:
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
    except Group.DoesNotExist:
        messages.error(request, "Delivery Crew group not found.")
        # Add redirect
        
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        # Add redirect
        
    if request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            form = DeliveryCrewForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                try:
                    user = User.objects.get(username=username)
                    if user in delivery_crew_group.user_set.all():
                        messages.info(request, f"User {username} is already in Delivery Crew group.")
                    elif user not in employee_group.user_set.all():
                        messages.error(request, f"User {username} must be an employee first.")
                    else:
                        delivery_crew_group.user_set.add(user)
                        messages.success(request, f"User {username} added to Delivery Crew group.")
                    return redirect('delivery_crew_view')
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
        else:
            messages.error(request, "Only managers and admins can add users to the Delivery Crew group.")
            return redirect('delivery_crew_view')
    else:
        form = DeliveryCrewForm()
        
    drivers = delivery_crew_group.user_set.all()
    context = {'drivers': drivers, 'form': form}
    return render(request, 'delivery_crew_view.html', context)


# Allows admin or managers to delete users from the Delivery Crew group
    # DELETE: Removes user from group
# Endpoint: /api/groups/delivery-crew/users/<str:username>
# View type: Function based, api
@api_view(['DELETE'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def delivery_crew_delete_api_view(request, username):
    try:
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
    except Group.DoesNotExist:
        return Response({"message": "Delivery Crew group not found."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        user = User.objects.get(username=username)
        if user in delivery_crew_group.user_set.all():
            delivery_crew_group.user_set.remove(user)
            return Response({"message": f"User {username} removed from Delivery Crew group. User {username} is still in the Employee group."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": f"User {username} is not in Delivery Crew group."}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# Allows admin or managers to delete users from the Delivery Crew group
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /groups/delivery-crew/users/<str:username>
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def delivery_crew_delete_view(request):
    try:
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
    except Group.DoesNotExist:
        messages.error(request, "Delivery Crew group not found.")
        # Add redirect
        
    if request.method == 'POST':
        form = DeliveryCrewForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in delivery_crew_group.user_set.all():
                    delivery_crew_group.user_set.remove(user)
                    messages.success(request, f"User {username} removed from Delivery Crew group. User {username} is still in Employee group.")
                else:
                    messages.info(request, f"User {username} is not in Delivery Crew group.")
                    return redirect('delivery_crew_delete_view')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = DeliveryCrewForm()
    
    drivers = delivery_crew_group.user_set.all()
    context = {'drivers': drivers, 'form': form}
    return render(request, 'delivery_crew_delete_view.html', context)


# Allows anyone to view categories
    # GET: Displays categories, 200
# Allows only admin or managers to add categories
    # POST: Adds a category, 201
# Endpoint: /api/category
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_api_view(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if request.user.is_authenticated and (request.user.groups.filter(name='Manager'.exists()) or request.user.is_superuser):
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Only managers and admins can add categories."}, status=status.HTTP_403_FORBIDDEN)       
    

# Allows anyone to view categories
    # GET: Displays categories
# Allows only admin or managers to add categories
    # POST: Adds a category
# Endpoint: /category
# View type: Function based, HTML
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_view(request):
    categories = Category.objects.all()
    form = CategoryForm()
    
    if request.method == 'POST':
        if request.user.is_authenticated and (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Category added successfully.")
                return redirect('category_view')
        else:
            messages.error(request, "Only managers and admin can add a category.")
        
    context = {'categories': categories, 'form': form}
    return render(request, 'category_view.html', context)


# Allows only managers or admin to delete categories
    # DELETE: Removes a category
# Endpoint: /api/category/delete/<slug:slug>
# View type: Function based, api
@api_view(['DELETE'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_delete_api_view(request, slug):
    try:
        category = get_object_or_404(Category, slug=slug)
        category.delete()
        return Response({"message": "Category deleted."}, status=status.HTTP_200_OK)
    except Category.DoesNotExist:
        return Response({"message": "Category not found."}, status=status.HTTP_404_NOT_FOUND)


# Allows only managers or admin to delete categories
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /category/delete/<slug:slug>
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_delete_view(request):
    categories = Category.objects.all()
    form = CategoryForm()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                category = Category.objects.get(slug=form.cleaned_data['slug'])
                category.delete()
                messages.success(request, "Category deleted successfully.")
            except Category.DoesNotExist:
                messages.error(request, "Category not found.")
            return redirect('category_delete_view')
        
    context = {'categories': categories, 'form': form}
    return render(request, 'category_delete_view.html', context)


# Allows anyone to view the items in each category
    # GET: Displays items in category
# Endpoint: /api/category/<slug:category_slug>
# View type: Function based, api
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([AllowAny, UserRateThrottle])
def category_details_api_view(request, category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        return Response({"message": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
    
    menu_items = MenuItem.objects.filter(category=category)
    category_serializer = CategorySerializer(category)
    menu_item_serializer = MenuItemSerializer(menu_items, many=True)
    
    return Response({
        "category": category_serializer.data,
        "menu_items": menu_item_serializer.data
    }, status=status.HTTP_200_OK)


# Allows anyone to view the items in each category
    # GET: Displays items in category
# Endpoint: /category/<slug:category_slug>
# View type: Function based, HTML
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_details_view(request, category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
        
    menu_items = MenuItem.objects.filter(category=category)
    
    context = {'category': category, 'menu_items': menu_items}
    return render(request, 'category_details_view.html', context)


# Allows anyone to view the menu
    # GET: Displays menu, 200
# Allows only managers or admin to add menu items
    # POST: Adds menu item, 201
# Endpoint: /api/menu
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_api_view(request):
    if request.method == 'GET':
        menu_items = MenuItem.objects.all()
        serializer = MenuItemSerializer(menu_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        if request.user.is_authenticated and (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
            serializer = MenuItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Only managers and admin can add menu items."})


# Allows anyone to view the menu
    # GET: Displays menu
# Allows only admin or managers to add items to the menu
    # POST (add_menu_item): Adds menu item
# Allows authenticated users to add items to their cart
    # POST (add_to_cart): Adds item to cart
# Endpoint: /menu
# View type: Function based, HTML
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_view(request):
    menu_items = MenuItem.objects.all()
    form = MenuItemForm()
    cart_form = CartForm()
    
    if request.method == 'POST':
        if request.user.is_authenticated and 'add_menu_item' in request.POST:
            if request.user.is_authenticated and (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
                form = MenuItemForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Menu item added successfully.")
                    return redirect('menu_view')
            else:
                messages.error(request, "Only managers and admin can add menu items.")
                
        elif request.user.is_authenticated and 'add_to_cart' in request.POST:
            cart_form = CartForm(request.POST)
            if cart_form.is_valid():
                cart_item = cart_form.save(commit=False)
                cart_item.user = request.user
                cart_item.save()
                messages.success(request, f"{cart_item.menuitem.title} added to your cart.")
                return redirect('menu_view')
            
    context = {'menu_items': menu_items, 'form': form, 'cart_form': cart_form}
    return render(request, 'menu_view.html', context)


# Allows anyone to view individual menu items
    # GET: Displays menu item, 200
# Allows authenticated user to add menu items to their cart
    # POST: Adds item to cart, sets the authenticated user as the user id for these cart items, 201
# Endpoint: /api/menu-item/<slug:slug>
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_item_api_view(request, slug):
    menu_item = get_object_or_404(MenuItem, slug=slug)
    
    if request.method == 'GET':
        serializer = MenuItemSerializer(menu_item)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({"message": "Authentication required to add items to the cart. Please log in or register."}, status=status.HTTP_401_UNAUTHORIZED)
        
        cart_serializer = CartSerializer(data=request.data, context={'request': request})
        if cart_serializer.is_valid():
            cart_serializer.save()
            return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
        return Response(cart_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Allows anyone to view individual menu items
    # GET: Displays menu item
# Allows authenticated users to add items to their cart
    # POST: Adds item to cart, sets the authenticated user as the user id for these cart items
# Endpoint: /menu-item/<slug:slug>
# View type: Function based, HTML
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_item_view(request, slug):
    menu_item = get_object_or_404(MenuItem, slug=slug)
    cart_form = CartForm(initial={'menuitem':menu_item})
    
    if request.method == 'POST' and request.user.is_authenticated:
        cart_form = CartForm(request.POST)
        if cart_form.is_valid():
            cart_item = cart_form.save(commit=False)
            cart_item.user = request.user
            cart_item.save()
            messages.success(request, f"{menu_item.title} added to cart.")
            return redirect('menu_item_view', slug=slug)
    
    context = {'menu_item': menu_item, 'cart_form': cart_form}
    return render(request, 'menu_item_view.html', context)


# Allows only managers or admin to delete menu items
    # DELETE: Removes menu item, 200
# Endpoint: /api/menu-item/delete/<slug:slug>
# View type: Function based, api
@api_view(['DELETE'])
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_item_delete_api_view(request, slug):
    try:
        menu_item = get_object_or_404(MenuItem, slug=slug)
        menu_item.delete()
        return Response({"message": "Menu item deleted."}, status=status.HTTP_200_OK)
    except MenuItem.DoesNotExist:
        return Response({"message": "MenuItem not found."}, status=status.HTTP_404_NOT_FOUND)
    
    
# Allows only managers or admin to delete menu items
    # POST: Removes menu item (forms only use GET and POST)
# Endpoint: /menu-item/delete/<slug:slug>
# View type: Function based, HTML
@login_required
@permission_classes([IsAdminOrManager])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_item_delete_view(request):
    menu_items = MenuItem.objects.all()
    form = MenuItemDeleteForm()
    
    if request.method == 'POST':
        form = MenuItemDeleteForm(request.POST)
        if form.is_valid():
            try:
                menu_item = MenuItem.objects.get(slug=form.cleaned_data['slug'])
                menu_item.delete()
                messages.success(request, "Menu item deleted successfully.")
            except MenuItem.DoesNotExist:
                messages.error(request, "Menu item not found.")
            return redirect('menu_item_delete_view')
    
    context = {'menu_items': menu_items, 'form': form}
    return render(request, 'menu_item_delete_view.html', context)


# Allows only the user to view, add, and remove menu items from their cart
    # GET: Displays menu item(s) already in cart, 200
    # POST: Adds menu item to cart, sets the authenticated user as the user id for these cart items, 201
    # DELETE: Removes item from user cart, 200
# Endpoint: /api/cart
# View type: Function based, api
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def cart_api_view(request):
    user = request.user
    
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart_items, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        menuitem_titles = request.data.get('menuitem_titles', [])
        if not menuitem_titles:
            return Response({"message": "Menu item name(s) required to delete."}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_titles = []
        for title in menuitem_titles:
            slug = slugify(title)
            try:
                menuitem = MenuItem.objects.get(slug=slug)
                cart_item = Cart.objects.get(user=user, menuitem=menuitem)
                cart_item.delete()
                deleted_titles.append(menuitem.title)
            except MenuItem.DoesNotExist:
                return Response({"message": f"Menu item '{title}' not found."}, status=status.HTTP_404_NOT_FOUND)
            except Cart.DoesNotExist:
                return Response({"message": f"Item '{title}' not found in your cart."}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({"message": f"Removed item(s) from cart: {', '.join(deleted_titles)}"}, status=status.HTTP_200_OK)
    
    
# Allows only the user to view, add, and remove menu items from their cart
    # GET: Displays items in the user's cart
    # POST (update_cart): Changes quantity of item in cart
    # POST (remove_selected): Removes selcted item(s) from cart
# Endpoint: /cart
# View type: Function based, HTML
def cart_view(request):
    user = request.user
    
    if request.method == 'POST':
        if 'update_cart' in request.POST:
            menuitem_id = request.POST.get('menuitem_id')
            new_quantity = int(request.POST.get('new_quantity'))
                
            try:
                menuitem = MenuItem.objects.get(id=menuitem_id)
                cart_item, created = Cart.objects.get(user=user, menuitem=menuitem)
                if new_quantity <= menuitem.inventory:
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    messages.success(request, f"Quantity of {menuitem.title} updated to {new_quantity}.")
                else:
                    messages.error(request, f"Requested quantity exceeds available stock for {menuitem.title}. Available stock: {menuitem.inventory}")
            except MenuItem.DoesNotExist:
                messages.error(request, "Menu item not found.")
            except Cart.DoesNotExist:
                messages.error(request, "Item not found in your cart.")
            return redirect('cart_view')
            
        elif 'remove_selected' in request.POST:
            selected_items = request.POST.getlist('selected_items')
            deleted_titles = []
            for item_id in selected_items:
                try:
                    menuitem = MenuItem.objects.get(id=item_id)
                    cart_item = Cart.objects.get(user=user, menuitem=menuitem)
                    cart_item.delete()
                    deleted_titles.append(menuitem.title)
                except MenuItem.DoesNotExist:
                    messages.error(request, "Menu item not found.")
                except Cart.DoesNotExist:
                    messages.error(request, f"Item '{menuitem.title}' not found in your cart.")
                    
            if deleted_titles:
                messages.success(request, f"Removed item(s) from your cart: {', '.join(deleted_titles)}")
            return redirect('cart_view')
        
    cart_items = Cart.objects.filter(user=user)
    context = {'cart_items': cart_items}
    return render(request, 'cart_view.html', context)
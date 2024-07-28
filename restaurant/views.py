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
from .models import Logger, UserComments, MenuItem, Category, Cart, Order, OrderItem, Booking
from .forms import LogForm, CommentForm, EmployeeForm, ManagerForm, DeliveryCrewForm, CategoryForm, MenuItemForm, MenuItemDeleteForm, CartForm, OrderUpdateForm, OrderAssignDeliveryCrewForm, BookingForm, ReservationStatusForm, DeleteReservationForm
from .permissions import IsAdmin, IsEmployee, IsAdminOrManager, IsAdminOrManagerOrEmployee, IsOwnerOrAdminOrManager, IsEmployeeOrAssignedDeliveryCrewOrCustomerOrAdmin, IsAdminOrEmployeeButNotDeliveryCrew
from .serializers import UserSerializer, UserRegSerializer, LoggerSerializer, UserCommentsSerializer, CategorySerializer, MenuItemSerializer, BookingSerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from datetime import datetime

# Create your views here.

# User registration
# Allows anyone to register for an account
    # POST: Must submit valid username, email, password, password verification. Creates new user, 201
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
# Allows only Admin, Managers, or the Employee the log belongs to, to check their shift hours/hours worked
    # GET: Admin and managers can view all logs, employees can only view their own logs, 200
# Allows only Employees to log their shift hours/hours worked
    # POST: Must submit valid first name, last name, and time. Creates a time log, 201
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
# Allows only Admin, Managers, or the Employee the log belongs to, to check their shift hours/hours worked
    # GET: Admin and managers can view all logs, employees can only view their own logs
# Allows only Employees to log their shift hours/hours worked
    # POST: Must submit valid first name, last name, and time. Creates a time log
# Endpoint: /restaurant/logger
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def logger_view(request):
    user = request.user
    
    if request.method == 'POST':
        if not user.groups.filter(name='Employee').exists() and not user.is_superuser:
            messages.error(request, "Only employees can log their shift hours.")
            return redirect('index') # Redirect after permission check
        
        form = LogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('logger_view') # Redirect to the same view to clear the form after submission
        
    else:
        form = LogForm()
        
    # Display logged hours
    if user.groups.filter(name='Manager').exists() or user.is_superuser:
        logs = Logger.objects.all()
    else:
        logs = Logger.objects.filter(first_name=user.first_name, last_name=user.last_name)
        
    context = {
        'form': form,
        'logs': logs
    }
    return render(request, 'logger.html', context)


# Home Page
# Allows anyone to view the homepage
    # GET: Displays the homepage
# Endpoint: /restaurant/index
# View Type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def index(request):
    current_year = datetime.now().year
    return render(request, 'index.html', {'current_year': current_year})


# Search API
# Allows anyone to search for titles from MenuItem and Category
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
# Allows anyone to search for titles from MenuItem and Category
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


# User comments API
# Allows anyone to view comments/reviews about the restaurant
    # GET: Displays previously posted comments, 200
# Allows only authenticated users to make comments/reviews about the restaurant
    # POST: Submits user comment/review, 201
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
# Allows only authenticated users to make comments/reviews about the restaurant
    # POST: Submits user comment/review
# Endpoint: /restaurant/comments
# View type: Function based, HTML, uses comments_api_view to fetch and display data
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def comments_view(request):
    form = CommentForm()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL) # Redirects to login for unauthorized users trying to POST
        form = CommentForm(request.POST)
        if form.is_valid():
            response = request.post(
                request.build_absolute_uri('/restaurant/comments'),
                data = form.cleaned_data,
                headers = {'Authorization': f'Token {request.user.auth_token.key}'}
            )
            if response.status_code == 201:
                return redirect('comments_view') # Redirect after successful form processing
            else:
                messages.error(request, "Error submitting comment.")
                return redirect('comments_view') # Redirect after exception handling
                
    response = request.get(request.build_absolute_uri('/restaurant/comments'))
    comments = response.json() if response.status_code == 200 else []
    
    context = {
        'form': form,
        'comments': comments
    }
    return render(request, 'comments.html', context)


# Allows only Admin and Managers to view users in Employee group
    # GET: Displays users in Employee group, 200
# Allows only Admin and Managers to add users to Employee group
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
        
        
# Allows only Admin and Managers to view users in Employee group
    # GET: Displays users in Employee group
# Allows only Admin and Managers to add users to Employee group
    # POST: Assigns user to the Employee group
# Endpoint: /groups/employee/users
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def employee_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to view or add users to the Employee group.")
        return redirect('index') # Redirect after permission check
    
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        return redirect('index') # Redirect after exception handling
        
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in employee_group.user_set.all():
                    messages.info(request, f"User {username} is already an employee.")
                    return redirect('employee_view') # Redirect after info message
                else:
                    employee_group.user_set.add(user)
                    messages.success(request, f"User {username} added to Employee Group.")
                    return redirect('employee_view') # Redirect after successful form processing
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('employee_view') # Redirect after exception handling
    else:
        form = EmployeeForm()
        
    employees = employee_group.user_set.all()
    context = {'employees': employees, 'form': form}
    return render(request, 'employee_view.html', context)
                
    
# Allows only Admin or Managers to delete users from the Employee group
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


# Allows only Admin or Managers to delete users from the Employee group
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /groups/employee/users/<str:username>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def employee_delete_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to remove users from the Employee group.")
        return redirect('employee_view') # Redirect after permission check
    
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        return redirect('index') # Redirect after exception handling
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in employee_group.user_set.all():
                    employee_group.user_set.remove(user)
                    messages.success(request, f"User {username} removed from Employee group.")
                    return redirect('employee_delete_view') # Redirect after successful form processing
                else:
                    messages.info(request, f"User {username} is not in Employee group.")
                    return redirect('employee_delete_view') # Redirect after info message
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('employee_delete_view') # Redirect after exception handling
    else:
        form = EmployeeForm()
        
    employees = employee_group.user_set.all()
    context = {'employees': employees, 'form': form}
    return render(request, 'employee_delete_view.html', context)


# Allows only Admin and Managers to view users in Manager group
    # GET: Displays users in Manager group, 200
# Allows only Admin and Managers to add users to Manager group if they are an Employee already
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
        
       
# Allows only Admin and Managers to view users in Manager group
    # GET: Displays users in Manager group
# Allows only Admin and Managers to add users to Manager group, if they are an Employee already
    # POST: Assigns user to the Manager group
# Endpoint: /groups/manager/users
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def manager_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to view or add users to the Manager group.")
        return redirect('index') # Redirect after permission check
    
    try:
        manager_group = Group.objects.get(name='Manager')
    except Group.DoesNotExist:
        messages.error(request, "Manager group not found.")
        return redirect('index') # Redirect after exception handling
        
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        return redirect('index') # Redirect after exception handling
    
    if request.method == 'POST':
        form = ManagerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in manager_group.user_set.all():
                    messages.info(request, f"User {username} is already a manager.")
                    return redirect('manager_view') # Redirect after info message
                elif user not in employee_group.user_set.all():
                    messages.error(request, f"User {username} must be an employee first.")
                    return redirect('manager_view') # Redirect after validation check
                else:
                    manager_group.user_set.add(user)
                    messages.success(request, f"User {username} added to Manager group.")
                    return redirect('manager_view') # Redirect after successful form processing
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('manager_view') # Redirect after exception handling
    else:
        form = ManagerForm()
        
    managers = manager_group.user_set.all()
    context = {'managers': managers, 'form': form}
    return render(request, 'manager_view.html', context)
        

# Allows only Admin or Managers to delete users from the Manager group
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
    

# Allows only Admin or Managers to delete users from the Manager group
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /groups/manager/users/<str:username>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def manager_delete_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to remove users from the Manager group.")
        return redirect('manager_view') # Redirect after permission check
    
    try:
        manager_group = Group.objects.get(name='Manager')
    except Group.DoesNotExist:
        messages.error(request, "Manager group not found.")
        return redirect('index') # Redirect after exception handling
    
    if request.method == 'POST':
        form = ManagerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in manager_group.user_set.all():
                    manager_group.user_set.remove(user)
                    messages.success(request, f"User {username} removed from Manager group. User {username} is still in the Employee group.")
                    return redirect('manager_delete_view') # Redirect after successful form processing
                else:
                    messages.info(request, f"User {username} is not in Manager group.")
                    return redirect('manager_delete_view') # Redirect after info message
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('manager_delete_view') # Redirect after exception handling
    else:
        form = ManagerForm()
        
    managers = manager_group.user_set.all()
    context = {'managers': managers, 'form': form}
    return render(request, 'manager_delete_view.html', context)


# Allows only Employees to view users in the Delivery Crew group
    # GET: Displays users in Delivery Crew group
# Allows only Admin and Managers to add users to the Delivery Crew group, if they are an Employee already
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
    
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        return Response({"message": "Employee group not found."}, status=status.HTTP_404_NOT_FOUND)
    
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
            

# Allows only Admin and Employees to view users in the Delivery Crew group
    # GET: Displays users in Delivery Crew group
# Allows only Admin and Managers to add users to the Delivery Crew group, if they are an Employee already
    # POST: Assigns user to Delivery Crew Group
# Endpoint: /groups/delivery-crew/users
# view type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def delivery_crew_view(request):
    if not (request.user.groups.filter(name='Employee').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to view the Delivery Crew group.")
        return redirect('index') # Redirect after permission check
    
    try:
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
    except Group.DoesNotExist:
        messages.error(request, "Delivery Crew group not found.")
        return redirect('index') # Redirect after exception handling
        
    try:
        employee_group = Group.objects.get(name='Employee')
    except Group.DoesNotExist:
        messages.error(request, "Employee group not found.")
        return redirect('index') # Redirect after exception handling
        
    if request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            form = DeliveryCrewForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                try:
                    user = User.objects.get(username=username)
                    if user in delivery_crew_group.user_set.all():
                        messages.info(request, f"User {username} is already in Delivery Crew group.")
                        return redirect('delivery_crew_view') # Redirect after info message
                    elif user not in employee_group.user_set.all():
                        messages.error(request, f"User {username} must be an employee first.")
                        return redirect('delivery_crew_view') # Redirect after validation check
                    else:
                        delivery_crew_group.user_set.add(user)
                        messages.success(request, f"User {username} added to Delivery Crew group.")
                        return redirect('delivery_crew_view') # Redirect after successful form processing
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
                    return redirect('delivery_crew_view') # Redirect after exception handling
        else:
            messages.error(request, "Only managers and admins can add users to the Delivery Crew group.")
            return redirect('delivery_crew_view') # Redirect after permission check
    else:
        form = DeliveryCrewForm()
        
    drivers = delivery_crew_group.user_set.all()
    context = {'drivers': drivers, 'form': form}
    return render(request, 'delivery_crew_view.html', context)


# Allows only Admin or Managers to delete users from the Delivery Crew group
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


# Allows only Admin or Managers to delete users from the Delivery Crew group
    # POST: Removes user from group with .remove (forms only use GET and POST)
# Endpoint: /groups/delivery-crew/users/<str:username>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def delivery_crew_delete_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to remove users from the Delivery Crew group.")
        return redirect('delivery_crew_view') # Redirect after permission check
    
    try:
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
    except Group.DoesNotExist:
        messages.error(request, "Delivery Crew group not found.")
        return redirect('index') # Redirect after exception handling
        
    if request.method == 'POST':
        form = DeliveryCrewForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            try:
                user = User.objects.get(username=username)
                if user in delivery_crew_group.user_set.all():
                    delivery_crew_group.user_set.remove(user)
                    messages.success(request, f"User {username} removed from Delivery Crew group. User {username} is still in Employee group.")
                    return redirect('delivery_crew_delete_view') # Redirect after successful form processing
                else:
                    messages.info(request, f"User {username} is not in Delivery Crew group.")
                    return redirect('delivery_crew_delete_view') # Redirect after info message
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('delivery_crew_delete_view') # Redirect after exception handling
    else:
        form = DeliveryCrewForm()
    
    drivers = delivery_crew_group.user_set.all()
    context = {'drivers': drivers, 'form': form}
    return render(request, 'delivery_crew_delete_view.html', context)


# Allows anyone to view categories
    # GET: Displays categories, 200
# Allows only Admin or Managers to add categories
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
# Allows only Admin or Managers to add categories
    # POST: Adds a category
# Endpoint: /category
# View type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_view(request):
    categories = Category.objects.all()
    form = CategoryForm()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL) # Redirect for unauthenticated users
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Category added successfully.")
                return redirect('category_view') # Redirect after successful form processing
        else:
            messages.error(request, "Only Managers and Admin can add a category.")
            return redirect('category_view') # Redirect after permission check
        
    context = {'categories': categories, 'form': form}
    return render(request, 'category_view.html', context)


# Allows only Admin or Managers to delete categories
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


# Allows only Admin or Managers to delete categories
    # POST: Removes a category (forms only use GET and POST)
# Endpoint: /category/delete/<slug:slug>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_delete_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to delete categories.")
        return redirect('category_view') # Redirect after permission check
    
    categories = Category.objects.all()
    form = CategoryForm()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                category = Category.objects.get(slug=form.cleaned_data['slug'])
                category.delete()
                messages.success(request, "Category deleted successfully.")
                return redirect('category_delete_view') # Redirect after successful form processing
            except Category.DoesNotExist:
                messages.error(request, "Category not found.")
                return redirect('category_delete_view') # Redirect after exception handling
        
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
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def category_details_view(request, category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
        return redirect('menu_view') # Redirect after exception handling
        
    menu_items = MenuItem.objects.filter(category=category)
    
    context = {'category': category, 'menu_items': menu_items}
    return render(request, 'category_details_view.html', context)


# Allows anyone to view the menu
    # GET: Displays menu, 200
# Allows only Admin or Managers to add menu items
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
# Allows only Admin or Managers to add items to the menu
    # POST (add_menu_item): Adds menu item
# Allows only authenticated users to add items to their cart
    # POST (add_to_cart): Adds item to cart
# Endpoint: /menu
# View type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_view(request):
    menu_items = MenuItem.objects.all()
    form = MenuItemForm()
    cart_form = CartForm()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL) # Redirect for unauthenticated users
        
        if 'add_menu_item' in request.POST:
            if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
                form = MenuItemForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Menu item added successfully.")
                    return redirect('menu_view') # Redirect after successful form processing
            else:
                messages.error(request, "Only managers and admin can add menu items.")
                return redirect('menu_view') # Redirect after permission check
                
        elif 'add_to_cart' in request.POST:
            cart_form = CartForm(request.POST)
            if cart_form.is_valid():
                cart_item = cart_form.save(commit=False)
                cart_item.user = request.user
                cart_item.save()
                messages.success(request, f"{cart_item.menuitem.title} added to your cart.")
                return redirect('menu_view') # Redirect after successful form processing
            
    context = {'menu_items': menu_items, 'form': form, 'cart_form': cart_form}
    return render(request, 'menu_view.html', context)


# Allows anyone to view individual menu items
    # GET: Displays menu item, 200
# Allows only authenticated users to add menu items to their cart
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
# Allows only authenticated users to add items to their cart
    # POST: Adds item to cart, sets the authenticated user as the user id for these cart items
# Endpoint: /menu-item/<slug:slug>
# View type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_item_view(request, slug):
    menu_item = get_object_or_404(MenuItem, slug=slug)
    cart_form = CartForm(initial={'menuitem':menu_item})
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('settings.LOGIN_URL') # Redirect for unauthenticated users
        
        cart_form = CartForm(request.POST)
        if cart_form.is_valid():
            cart_item = cart_form.save(commit=False)
            cart_item.user = request.user
            cart_item.save()
            messages.success(request, f"{menu_item.title} added to cart.")
            return redirect('menu_item_view', slug=slug) # Redirect after successful form processing
    
    context = {'menu_item': menu_item, 'cart_form': cart_form}
    return render(request, 'menu_item_view.html', context)


# Allows only Admin or Managers to delete menu items
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
    
    
# Allows only Admin or Managers to delete menu items
    # POST: Removes menu item (forms only use GET and POST)
# Endpoint: /menu-item/delete/<slug:slug>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_item_delete_view(request):
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        messages.error(request, "You do not have permission to remove this menu item.")
        return redirect('menu_view') # Redirect after permission check
    
    menu_items = MenuItem.objects.all()
    form = MenuItemDeleteForm()
    
    if request.method == 'POST':
        form = MenuItemDeleteForm(request.POST)
        if form.is_valid():
            try:
                menu_item = MenuItem.objects.get(slug=form.cleaned_data['slug'])
                menu_item.delete()
                messages.success(request, "Menu item deleted successfully.")
                return redirect('menu_item_delete_view') # Redirect after successful form processing
            except MenuItem.DoesNotExist:
                messages.error(request, "Menu item not found.")
                return redirect('menu_item_delete_view') # Redirect after exception handling
    
    context = {'menu_items': menu_items, 'form': form}
    return render(request, 'menu_item_delete_view.html', context)


# Allows only the authenticated user to view menu items in their cart
    # GET: Displays menu item(s) already in cart, 200
# Allows only the authenticated user to add menu items to their cart
    # POST: Adds menu item to cart, sets the authenticated user as the user id for these cart items, 201
# Allows only the authenticated user to remove menu items from their cart
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
    
  
# Allows only the authenticated user to view menu items in their cart
    # GET: Displays items in the user's cart
# Allows only the authenticated user to add menu items to their cart
    # POST (update_cart): Changes quantity of item in cart
# Allows only the authenticated user to remove menu items from their cart
    # POST (remove_selected): Removes selcted item(s) from cart
# Endpoint: /cart
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def cart_view(request):
    user = request.user
    
    if not user.is_authenticated:
        return redirect('settings.LOGIN_URL') # Redirect to login for unauthenticated users
    
    if request.method == 'POST':
        if 'update_cart' in request.POST:
            menuitem_id = request.POST.get('menuitem_id')
            new_quantity = int(request.POST.get('new_quantity'))
                
            try:
                menuitem = MenuItem.objects.get(id=menuitem_id)
                cart_item = Cart.objects.get(user=user, menuitem=menuitem)
                if new_quantity <= menuitem.inventory:
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    messages.success(request, f"Quantity of {menuitem.title} updated to {new_quantity}.")
                    return redirect('cart_view') # Redirect after successful form processing
                else:
                    messages.error(request, f"Requested quantity exceeds available stock for {menuitem.title}. Available stock: {menuitem.inventory}")
                    return redirect('cart_view') # Redirect after error message
            except MenuItem.DoesNotExist:
                messages.error(request, "Menu item not found.")
                return redirect('cart_view') # Redirect after exception handling
            except Cart.DoesNotExist:
                messages.error(request, f"Item '{menuitem.title}' not found in your cart.")
                return redirect('cart_view') # Redirect after exception handling
            
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
                    return redirect('cart_view') # Redirect after exception handling
                except Cart.DoesNotExist:
                    messages.error(request, f"Item '{menuitem.title}' not found in your cart.")
                    return redirect('cart_view') # Redirect after exception handling
                    
            if deleted_titles:
                messages.success(request, f"Removed item(s) from your cart: {', '.join(deleted_titles)}")
            return redirect('cart_view') # Redirect after successful form processing
        
    cart_items = Cart.objects.filter(user=user)
    cart_subtotal = sum(item.price for item in cart_items)
    cart_price_after_tax = cart_subtotal * Decimal(1.1)
    serializer = CartSerializer(cart_items, many=True, context={'request': request})
    context = {
        'cart_items': serializer.data,
        'cart_subtotal': "{:.2f}".format(cart_subtotal),
        'cart_price_after_tax': "{:.2f}".format(cart_price_after_tax),
    }
    return render(request, 'cart_view.html', context)


# Allows only Employees other than Delivery Crew to view all orders. Allows Delivery Crew to view only the orders assigned to them
    # GET: Displays orders, 200
# Allows only authenticated users to create an order
    # POST: Creates new order for current user, gets cart items, adds them to the order, then deletes them from the cart for the user, 201
# Endpoint: /api/orders
# View type: Function based, api
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsEmployeeOrAssignedDeliveryCrewOrCustomerOrAdmin])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def orders_api_view(request):
    user = request.user
    
    if request.method == 'GET':
        if user.is_superuser or user.groups.filter(name='Employee').exists():
            if user.groups.filter(name='Delivery Crew').exists():
                # Delivery Crew can only view orders assigned to them
                orders = Order.objects.filter(delivery_crew=user)
            else:
                # Employees (excluding Delivery Crew) can view all orders
                orders = Order.objects.all()
        else:
            # Customers can view only their own orders
            orders = Order.objects.filter(user=user)
        
        serializer = OrderSerializer(orders, many=True, context={'request', request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"message": "Cart is empty. Please add items to your cart to place an order."}, status=status.HTTP_400_BAD_REQUEST)
        
        total = sum(item.menuitem.price * item.quantity for item in cart_items)
        order_data = {
            'user': user.id,
            'order_status': False,
            'ready_for_delivery': False,
            'total': total,
            'time': timezone.now().date()
        }
        serializer = OrderSerializer(data=order_data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            for item in cart_items:
                OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity)
            cart_items.delete()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# Allows only Employees other than Delivery Crew to view all orders. Allows Delivery Crew to view only the orders assigned to them
    # GET: Displays orders
# Allows only authenticated users to create an order
    # POST: Creates new order for current user, gets cart items, adds them to the order, then deletes them from the cart for the user
# Endpoint: /orders
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def orders_view(request):
    user = request.user
    
    if request.method == 'POST':
        if 'create_order' in request.POST:
            if not user.is_authenticated:
                return redirect('settings.LOGIN_URL') # Redirect to login for unauthenticated users
            
            cart_items = Cart.objects.filter(user=user)
            if not cart_items.exists():
                messages.error(request, "Cart is empty. Please add items to your cart to place an order.")
                return redirect('orders_view')  # Redirect after exception handling
        
            total = sum(item.menuitem.price * item.quantity for item in cart_items)
            order = Order.objects.create(
                user=user,
                order_status=False,
                ready_for_delivery=False,
                total=total,
                time=timezone.now().date()
            )
        
            for item in cart_items:
                OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity)
                
            cart_items.delete()
            messages.success(request, "Order placed successfully.")
            return redirect('orders_view') # Redirect after successful form processing
            
    if user.is_superuser or user.groups.filter(name='Employee').exists():
        if user.groups.filter(name='Delivery Crew').exists():
            # Delivery Crew can only view orders assigned to them
            orders = Order.objects.filter(delivery_crew=user)
        else:
            # Employees (excluding Delivery Crew) can view all orders
            orders = Order.objects.all()
    else:
        # Customers can view only their own orders
        orders = Order.objects.filter(user=user)
        
    context = {'orders': orders}
    return render(request, 'orders_view.html', context)


# Allows only Admin, Employees, and the user who created the order to view the order details
    # GET: Displays order details, 200
# Allows only Admin, Employees other than Delivery Crew to assign Delivery Crew to order
    # PUT: Assigns Delivery Crew user to order, allowing them access to that order for various purposes, 200
# Allows only Admin and Employees other than Delivery Crew to update ready_for_delivery
    # PATCH: Updates ready_for_delivery, 0 (False, not ready for delivery) or 1 (True, ready for delivery), 200
# Allows only Admin, Managers, or Delivery Crew to update order status
    # PATCH: Updates order status, 0 (False, not yet delivered) or 1 (True, delivered), 200
# Allows only Admin or Managers to delete the order
    # DELETE: Deletes order, 200
# Endpoint: /api/orders/<int:order_id>
# View type: Function based, api
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsEmployeeOrAssignedDeliveryCrewOrCustomerOrAdmin])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def order_details_api_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'GET':
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not request.user.groups.filter(name='Delivery Crew').exists():
            serializer = OrderSerializer(order, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Delivery Crew cannot assign Delivery Crew to orders."}, status=status.HTTP_403_FORBIDDEN)
        
    elif request.method == 'PATCH':
        if 'ready_for_delivery' in request.data:
            if not request.user.groups.filter(name='Delivery Crew').exists():
                order.ready_for_delivery = request.data['ready_for_delivery']
                order.save()
                return Response({"message": "Order ready-for-delivery status updated."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Delivery Crew cannot update this status."}, status=status.HTTP_403_FORBIDDEN)
            
        if 'order_status' in request.data:
            if request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(name='Delivery Crew').exists() or request.user.is_superuser:
                order.order_status = request.data['order_status']
                order.save()
                return Response({"message": "Order delivery status updated."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Only Delivery Crew, Managers, or Admin can update delivery status."}, status=status.HTTP_403_FORBIDDEN)
            
    elif request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            order.delete()
            return Response({"message": "Order deleted."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Only Managers or Admin can delete orders."}, status=status.HTTP_403_FORBIDDEN)
        

# Allows only Admin, Employees, and the authenticated user who created the order to view the order details
    # GET: Displays order details
# Allows only Admin and Employees other than Delivery Crew to update ready_for_delivery
    # POST (update_order): Updates ready_for_delivery, 0 (False, not ready for delivery) or 1 (True, ready for delivery)
# Allows only Admin, and Employees other than Delivery Crew to assign Delivery Crew to order
    # POST (assign_delivery_crew): Assigns Delivery Crew user to order, allowing them access to that order for various purposes
# Allows only Admin, Managers, or Delivery Crew to update order status
    # POST (order_status): Updates order status, 0 (False, not yet delivered) or 1 (True, delivered)
# Allows only Admin or Managers to delete the order
    # POST (delete_order): Deletes order
# Uses .has_permission for conditional auth
# Endpoint: /orders/<int:order_id>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def order_details_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user = request.user
    
    if not IsEmployeeOrAssignedDeliveryCrewOrCustomerOrAdmin().has_permission(request, view=None):
        messages.error(request, "You do not have permission to view this order.")
        return redirect('orders_view') # Redirect after permission check
    
    if request.method == "POST":
        if not user.is_authenticated:
            return redirect('settings.LOGIN_URL') # Redirect to login for unauthenticated users
        
        if 'update_order' in request.POST:
            if user.groups.filter(name='Delivery Crew').exists() and not user.is_superuser:
                messages.error(request, "You do not have permission to update this order.")
                return redirect('order_details_view', order_id=order.id) # Redirect after permission check
            else:
                form = OrderUpdateForm(request.POST, instance=order)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Ready for Delivery status updated successfully.")
                    return redirect('order_details_view', order_id=order.id) # Redirect after successful form processing
                else:
                    messages.error(request, "There was an error updating Ready for Delivery status for this order.")
                    return redirect('order_details_view', order_id=order.id) # Redirect after form error
                    
        elif 'assign_delivery_crew' in request.POST:
            if user.groups.filter(name='Delivery Crew').exists() and not user.is_superuser:
                messages.error(request, "You do not have permission to assign Delivery Crew to orders.")
                return redirect('order_details_view', order_id=order.id) # Redirect after permission check
            else:
                form = OrderAssignDeliveryCrewForm(request.POST)
                if form.is_valid():
                    delivery_crew_username = form.cleaned_data.get('delivery_crew_username')
                    try:
                        delivery_crew = User.objects.get(username=delivery_crew_username)
                        if not delivery_crew.groups.filter(name='Delivery Crew').exists():
                            messages.error(request, "User is not a Delivery Crew member.")
                            return redirect('order_details_view', order_id=order.id) # Redirect after validation check
                        else:
                            order.delivery_crew = delivery_crew
                            order.save()
                            messages.success(request, "Delivery Crew assigned successfully.")
                            return redirect('order_details_view', order_id=order.id) # Redirect after successful form processing
                    except User.DoesNotExist:
                        messages.error(request, "User not found.")
                        return redirect('order_details_view', order_id=order.id) # Redirect after exception handling
                else:
                    messages.error(request, "There was an error assigning the delivery crew.")
                    return redirect('order_details_view', order_id=order.id) # Redirect after form processing error
            
        elif 'order_status' in request.POST:
            if user.groups.filter(name='Manager').exists() or user.groups.filter(name='Delivery Crew').exists() or user.is_superuser:
                form = OrderUpdateForm(request.POST, instance=order)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Order delivery status updated successfully.")
                    return redirect('order_details_view', order_id=order.id) # Redirect after successful form processing
                else:
                    messages.error(request, "There was an error updating the order delivery status.")
                    return redirect('order_details_view', order_id=order.id) # Redirect after form processing error
            else:
                messages.error(request, "You do not have permission to update the order delivery status.")
                return redirect('order_details_view', order_id=order.id) # Redirect after permission check
        
        elif 'delete_order' in request.POST:
            if user.groups.filter(name='Manager').exists() or user.is_superuser:
                order.delete()
                messages.success(request, "Order deleted successfully.")
                return redirect('orders_view') # Redirect after successful form processing
            else:
                messages.error(request, "You do not have permission to delete this order.")
                return redirect('order_details_view', order_id=order.id) # Redirect after permission check
                
        return redirect('order_details_view', order_id=order.id)
    
    order_update_form = OrderUpdateForm(instance=order)
    assign_delivery_crew_form = OrderAssignDeliveryCrewForm()
    
    context = {
        'order': order,
        'order_update_form': order_update_form,
        'assign_delivery_crew_form': assign_delivery_crew_form
    }
    
    return render(request, 'order_details_view.html', context)


# Business hours dictionary with days as keys and tuples of open and close hours as values
BUSINESS_HOURS = {
    0: (11, 21), # Monday
    1: (11, 21), # Tuesday
    2: (11, 21), # Wednesday
    3: (11, 21), # Thursday
    4: (11, 21), # Friday
    5: (11, 22), # Saturday
    6: (12, 20) # Sunday
}


# Allows anyone to book a reservation during business hours (up to 1 hour before close)
    # POST: Creates a booking, 201
# Endpoint: /api/bookings
# View type: Function based, api
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def booking_api_view(request):
    serializer = BookingSerializer(data=request.data)
    if serializer.is_valid():
        booking_date = serializer.validated_data['booking_date']
        day_of_week = booking_date.weekday()
        open_hour, close_hour = BUSINESS_HOURS[day_of_week]
        
        if not open_hour <= booking_date.hour < close_hour -1:
            return Response(
                {"message": "Bookings can only be made during business hours and up to an hour before closing."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Allows anyone to view the booking page
    # GET: Displays booking page
# Allows anyone to book a reservation during business hours (up to 1 hour before close)
    # POST: Creates a reservation
# Endpoint: /bookings
# View type: Function based, HTML
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def booking_view(request):
    form = BookingForm()
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking_date = form.cleaned_data['booking_date']
            day_of_week = booking_date.weekday()
            
            open_hour, close_hour = BUSINESS_HOURS[day_of_week]
            
            if not (open_hour <= booking_date.hour < close_hour - 1):
                messages.error(request, "Bookings can only be made during business hours and up to an hour before closing.")
                return redirect('booking_view') # Redirect after validation check
            else:
                form.save()
                messages.success(request, "Booking made successfully.")
                return redirect('reservation_details_view') # Redirect after successful form processing
        else:
            messages.error(request, "There was an error with your booking.")
            return redirect('booking_view') # Redirect after form processing error
            
    business_hours = {
        'Weekdays': '11am - 9pm',
        'Sat': '11am - 10pm',
        'Sun': '12pm - 8pm'
    }
    
    context = {'form': form, 'business_hours': business_hours}
    
    return render(request, 'booking_view.html', context)


# Allows only Admin or Employees (excluding Delivery Crew) to view current reservations that have been made
    # GET: Displays currently booked reservations, 200
# Endpoint: /api/reservations
# View type: Function based, api
@api_view(['GET'])
@permission_classes([IsAdminOrEmployeeButNotDeliveryCrew])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def reservations_api_view(request):
    bookings = Booking.objects.filter(reservation_status='current')
    if not bookings.exists():
        return Response({"message": "No current reservations."}, status=status.HTTP_200_OK)
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Allows only Admin or Employees (excluding Delivery Crew) to view current reservations that have been made
    # GET: Displays currently booked reservations
# Uses .has_permission for conditional auth
# Endpoint: /reservations
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def reservations_view(request):
    if not IsAdminOrEmployeeButNotDeliveryCrew().has_permission(request, view=None):
        messages.error(request, "You do not have permission to view reservations.")
        return redirect('index') # Redirect after permission check
    
    bookings = Booking.objects.filter(reservation_status='current')
    context = {'bookings': bookings}
    if not bookings.exists():
        context['no_reservations_message'] = "No current reservations."
    return render(request, 'reservations_view.html', context)


# Allows only Admin or Employees (excluding Delivery Crew) to view past reservations that have been made (either completed or missed)
    # GET: Displays past reservations, 200
# Endpoint: /api/reservations/old
# View type: Function based, api
@api_view(['GET'])
@permission_classes([IsAdminOrEmployeeButNotDeliveryCrew])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def old_reservations_api_view(request):
    bookings = Booking.objects.filter(reservation_status__in=['completed', 'missed'])
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Allows only Admin or Employees (excluding Delivery Crew) to view past reservations that have been made (either completed or missed)
    # GET: Displays past reservations
# Uses .has_permission for conditional auth
# Endpoint: /reservations/old
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def old_reservations_view(request):
    if not IsAdminOrEmployeeButNotDeliveryCrew().has_permission(request, view=None):
        messages.error(request, "You do not have permission to view reservations.")
        return redirect('index') # Redirect after permission check
    
    bookings = Booking.objects.filter(reservation_status__in=['completed', 'missed'])
    context = {'bookings': bookings}
    return render(request, 'old_reservations_view.html', context)


# Allows only Admin or Employees (excluding Delivery Crew) and the user who created the booking to view reservation details
    # GET: Displays reservation details, 200
# Allows only Admin or Employees (excluding Delivery Crew) to change the status of a reservation
    # POST: Sets the status of a reservation, 201
# Allows only Admin or Managers to remove a reservation
    # DELETE: Removes a reservation
# Endpoint: /api/reservations/<int:reservation_id>
# View type: Function based, api
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def reservation_details_api_view(request, reservation_id):
    booking = get_object_or_404(Booking, id=reservation_id)
    user = request.user
    
    if request.method == 'GET':
        if not (user.groups.filter(name='Employee').exclude(name='Delivery Crew').exists() or user.is_superuser or booking.name == user.get_full_name()):
            return Response({"message": "You do not have permission to view this reservation."}, status=status.HTTP_403_FORBIDDEN)
        serializer = BookingSerializer(booking)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not (user.groups.filter(name='Employee').exclude(name='Delivery Crew').exists() or user.is_superuser):
            return Response({"message": "You do not have permission to update this reservation."}, status=status.HTTP_403_FORBIDDEN)
        
        reservation_status = request.data.get('reservation_status')
        if reservation_status not in ['completed', 'missed']:
            return Response({"message": "Invalid status. Choose either 'completed' or 'missed'."}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.reservation_status = reservation_status
        booking.save()
        return Response({"message": "Reservation status updated successfully."})
    
    elif request.method == 'DELETE':
        if not (user.groups.filter(name='Manager').exists() or user.is_superuser):
            return Response({"message": "You do not have permission to delete this reservation."}, status=status.HTTP_403_FORBIDDEN)
        
        booking.delete()
        return Response({"message": "Reservation deleted successfully."}, status=status.HTTP_200_OK)
    
    
# Allows only Admin or Employees (excluding Delivery Crew) and the authenticated user who created the booking to view reservation details
    # GET: Displays reservation details
# Allows only Admin or Employees (excluding Delivery Crew) to change the status of a reservation
    # POST: Sets the status of a reservation
# Allows only Managers or Admin to delete reservations
    # POST: Removes a reservation
# Endpoint: /reservations/<int:reservation_id>
# View type: Function based, HTML
@login_required
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def reservation_details_view(request, reservation_id):
    reservation = get_object_or_404(Booking, id=reservation_id)
    user = request.user
    
    if not (user.groups.filter(name='Employee').exists() or reservation.user == user or user.is_superuser):
        messages.error(request, "You do not have permission to view this reservation.")
        return redirect('index') # Redirect after permission check
    
    if request.method == 'POST':
        if not user.is_authenicated:
            return redirect('settings.LOGIN_URL') # Redirect to login for unauthenticated users
        
        if 'reservation_status' in request.POST:
            if user.groups.filter(name='Employee').exclude(name='Delivery Crew').exists() or user.is_superuser:
                form = ReservationStatusForm(request.POST, instance=reservation)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Reservation status updated successfully.")
                    return redirect('reservation_details_view', reservation_id=reservation.id) # Redirect after successful form processing
                else:
                    messages.error(request, "There was an error updating reservation status.")
                    return redirect('reservation_details_view', reservation_id=reservation.id) # Redirect after form processing error
            else:
                messages.error(request, "You do not have permission to change reservation status.")
                return redirect('reservation_details_view', reservation_id=reservation.id)
            
        elif 'remove_selected' in request.POST:
            if user.groups.filter(name='Manager').exists() or user.is_superuser:
                form = DeleteReservationForm(request.POST)
                if form.is_valid():
                    reservation.delete()
                    messages.success(request, "Reservation deleted successfully.")
                    return redirect('reservations_view') # Redirect after successful form processing
                else:
                    messages.error(request, "There was an error deleting the reservation.")
                    return redirect('reservation_details_view', reservation_id=reservation.id) # Redirect after form processing error
            else:
                messages.error(request, "You do not have permission to delete reservations. If you are the customer who made the reservation, please contact management.")
                return redirect('reeservation_details_view', reservation_id=reservation.id) # Redirect after permission check
            
    reservation_status_form = ReservationStatusForm(instance=reservation)
    delete_reservation_form = DeleteReservationForm()
    
    context = {
        'reservation': reservation,
        'reservation_status_form': reservation_status_form,
        'delete_reservation_form': delete_reservation_form
    }
    
    return render(request, 'reservation_details_view.html', context)
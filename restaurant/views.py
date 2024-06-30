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
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes, throttle_classes
from rest_framework.renderers import TemplateHTMLRenderer, StaticHTMLRenderer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication # Might not need
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status, viewsets, generics
from decimal import Decimal
from .models import Logger, UserComments, MenuItem, Category, Cart, Order, OrderItem
from .forms import LogForm, CommentForm, EmployeeForm, ManagerForm, DeliveryCrewForm
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
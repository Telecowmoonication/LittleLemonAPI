from django import forms
from django.contrib.auth.models import User
from .models import Logger, UserComments, Category, MenuItem, Cart, Order, Booking
import datetime
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm

# Form for users to enter their registration info
class UserRegForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, validators=[validate_password])
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
            
        if password != password2:
            raise forms.ValidationError("Password fields did not match.")
            
        return cleaned_data
        
        
# Form to update user info
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email
        

# Form users fill out to get an Auth token
class AuthTokenForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    
# Form users fill out to login
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


# Form for employee logs
class LogForm(forms.ModelForm):
    class Meta:
        model = Logger
        fields = '__all__'
        
  
# Form for user comments
class CommentForm(forms.ModelForm):
    class Meta:
        model = UserComments
        fields = '__all__'


# Form for adding or removing employees
class EmployeeForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Enter the username of the user to be added/removed as an employee.")
    
    class Meta:
        model = User
        fields = ['username']

        
# Form for adding or removing managers
class ManagerForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Enter the username of the user to be added/removed as a manager.")
    
    class Meta:
        model = User
        fields = ['username']

    
# Form for adding or removing delivery crew
class DeliveryCrewForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Ener the username of the user to be added/removed as delivery crew.")
    
    class Meta:
        model = User
        fields = ['username']


# Form for adding categories
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['slug', 'title']
        
# Form for removing categories
class CategoryDeleteForm(forms.ModelForm):
    slug = forms.SlugField(max_length=255, help_text="Enter the slug of the category to be deleted.")
    
    class Meta:
        model = Category
        fields = ['slug']
        
        
# Form for adding menu items
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['slug', 'title', 'unit_price', 'featured', 'category', 'inventory']
        
        
# Form for removing menu items
class MenuItemDeleteForm(forms.ModelForm):
    slug = forms.SlugField(max_length=255, help_text="Enter the slug of the menu item to be deleted.")
    
    class Meta:
        model = MenuItem
        fields = ['slug']
        

# Form for users to update their cart
class CartForm(forms.ModelForm):
    menuitem_title = forms.CharField(max_length=255)
    quantity = forms.IntegerField(min_value=1)
    
    class Meta:
        model = Cart
        fields = ['menuitem', 'quantity']
        
        
# Might not need
# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = ['user', 'delivery_crew', 'order_status', 'ready_for_delivery', 'total', 'time']
        
        
# Form for updating order and delivery statuses
class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status', 'ready_for_delivery']
        widgets = {
            'order_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ready_for_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'order_status': 'Delivered',
            'ready_for_delivery': 'Ready for Delivery'
        }
        
        
# Form for assigning Delivery Crew to an order
class OrderAssignDeliveryCrewForm(forms.Form):
    delivery_crew_username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        labels = {
            'delivery_crew_username': 'Delivery Crew Username'
        }
        
        
# Form for users to book a reservation
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'no_of_guests', 'booking_date']
        
    def clean_booking_date(self):
        booking_date = self.cleaned_data['booking_date']
        days_of_week = booking_date.weekday()
        BUSINESS_HOURS = {
            0: (11, 21), # Monday
            1: (11, 21), # Tuesday
            2: (11, 21), # Wednesday
            3: (11, 21), # Thursday
            4: (11, 21), # Friday
            5: (11, 22), # Saturday
            6: (12, 20) # Sunday
        }
        
        open_hour, close_hour = BUSINESS_HOURS[days_of_week]
        
        if not (open_hour <= booking_date.hour < close_hour -1):
            raise forms.ValidationError("Bookings can only be made during business hours and up to an hour before closing.")
        
        if booking_date < datetime.datetime.now():
            raise forms.ValidationError("Booking date must be in the future.")
        
        return booking_date
    
    
# Form for updating reservation status of a booking
class ReservationStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['reservation_status']
        

# Form for deleting reservations
class DeleteReservationForm(forms.Form):
    confirm_deletion = forms.BooleanField(required=True)
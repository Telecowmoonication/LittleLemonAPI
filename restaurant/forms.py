from django import forms
from django.contrib.auth.models import User
from .models import Logger, UserComments, Category, MenuItem, Cart, Order, Booking
import datetime

class LogForm(forms.ModelForm):
    class Meta:
        model = Logger
        fields = '__all__'
        
  
class CommentForm(forms.ModelForm):
    class Meta:
        model = UserComments
        fields = '__all__'


class EmployeeForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Enter the username of the user to be added/removed as an employee.")
    
    class Meta:
        model = User
        fields = ['username']

        
class ManagerForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Enter the username of the user to be added/removed as a manager.")
    
    class Meta:
        model = User
        fields = ['username']

    
class DeliveryCrewForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Ener the username of the user to be added/removed as a manager.")
    
    class Meta:
        model = User
        fields = ['username']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['slug', 'title']
        
        
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['slug', 'title', 'unit_price', 'featured', 'category', 'inventory']
        
        
class MenuItemDeleteForm(forms.ModelForm):
    slug = forms.SlugField(max_length=255, help_text="Enter the slug of the menu item to be deleted.")
    
    class Meta:
        model = MenuItem
        fields = ['slug']
        

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
        
        
class OrderAssignDeliveryCrewForm(forms.Form):
    delivery_crew_username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        labels = {
            'delivery_crew_username': 'Delivery Crew Username'
        }
        
        
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
    
    
class ReservationStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['reservation_status']
        

class DeleteReservationForm(forms.Form):
    confirm_deletion = forms.BooleanField(required=True)
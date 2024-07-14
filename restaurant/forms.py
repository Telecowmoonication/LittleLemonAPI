from django import forms
from django.contrib.auth.models import User
from .models import Logger, UserComments, Category, MenuItem, Cart, Order

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
        fields = ['title', 'price', 'featured', 'category', 'inventory']
        
        
class MenuItemDeleteForm(forms.ModelForm):
    slug = forms.SlugField(max_length=255, help_text="Enter the slug of the menu item to be deleted.")
    
    class Meta:
        model = MenuItem
        fields = ['slug']
        

class CartForm(forms.ModelForm):
    menuitem_title = forms.CharField(max_length=255)
    quantity = forms.IntegerField(min_value=1)
    
    class Meta:
        mdoel = Cart
        fields = ['menuitem', 'quantity']
        
        
# Might not need
# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = ['user', 'delivery_crew', 'status', 'ready_for_delivery', 'total', 'time']
        
        
class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'ready_for_delivery']
        widgets = {
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ready_for_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'status': 'Delivered',
            'ready_for_delivery': 'Ready for Delivery'
        }
        
        
class OrderAssignDeliveryCrewForm(forms.Form):
    delivery_crew_username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        labels = {
            'delivery_crew_username': 'Delivery Crew Username'
        }
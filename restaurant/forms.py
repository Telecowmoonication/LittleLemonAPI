from django import forms
from django.contrib.auth.models import User
from .models import Logger, UserComments, Category, MenuItem

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
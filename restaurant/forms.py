from django import forms
from django.contrib.auth.models import User
from .models import Logger, UserComments

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

        
class ManagerForm(forms.form):
    username = forms.Charfield(max_length=255, help_text="Enter the username of the user to be added/removed as a manager.")
    
    class Meta:
        model = User
        fields = ['username']

    
class DeliveryCrewForm(forms.ModelForm):
    username = forms.CharField(max_length=255, help_text="Ener the username of the user to be added/removed as a manager.")
    
    class Meta:
        model = User
        fields = ['username']
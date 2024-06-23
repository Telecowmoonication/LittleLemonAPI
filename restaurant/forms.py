from django import forms
from .models import Logger, UserComments

class LogForm(forms.ModelForm):
    class Meta:
        model = Logger
        fields = '__all__'
        
  
class CommentForm(forms.ModelForm):
    class Meta:
        model = UserComments
        fields = '__all__'
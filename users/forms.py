from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'mitsulist-input'}),
            'email': forms.EmailInput(attrs={'class': 'mitsulist-input'}),
        }

from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'gender', 'birth_date']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'mitsulist-input', 'rows': 4}),
            'gender': forms.Select(attrs={'class': 'mitsulist-input'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'mitsulist-input', 'style': 'color-scheme: dark;'}),
            'image': forms.FileInput(attrs={'class': 'mitsulist-input'}),
        }

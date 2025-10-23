from django import forms
from django.contrib.auth.models import User
from .models import Member, Coach

# REGISTRATION FORMS

class MemberRegistrationForm(forms.ModelForm):
    # User fields
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Member
        fields = ['profile_photo', 'city', 'phone']

    # Check if username taken
    def clean_username(self):
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        
        return username
    
    # Check if passwords match
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        
        return password_confirm

class CoachRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Coach
        fields = ['profile_photo', 'city', 'phone', 'sport', 'hourly_fee']

    # Check if username taken
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        
        return username
    
    # Check if passwords match
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        
        return password_confirm
    
# PROFILE EDITING FORMS

# Form to edit the User's built-in fields
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# Form to edit the Member's profile fields
class MemberEditForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['profile_photo', 'city', 'phone']

# Form to edit the Coach's profile fields
class CoachEditForm(forms.ModelForm):
    class Meta:
        model = Coach
        fields = ['profile_photo', 'city', 'phone', 'sport', 'hourly_fee']
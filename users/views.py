from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Member, Coach


from .forms import (
    MemberRegistrationForm,
    CoachRegistrationForm,
    UserEditForm,
    MemberEditForm,
    CoachEditForm
)
from .models import Member, Coach

# Create your views here.

# REGISTRATION VIEWS

@transaction.atomic # Ensures User and Profile are created successfully
def register_member(request):
    form = MemberRegistrationForm(request.POST)

    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        
        if form.is_valid():
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data.get('username'),
                email=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name')
            )

            # Create Member and link it to user
            member = form.save(commit=False)
            member.user = user
            member.save()

            # Log the user in and redirect
            login (request, user)
            messages.success(request, 'Successfully registered as Member!')
            return redirect('users:show_profile')
        else:
            form = MemberRegistrationForm

    context = {'form': form}
    return render(request, 'register_member.html', context)
    
@transaction.atomic # Ensures User and Profile are created successfully
def register_coach(request):
    form = CoachRegistrationForm(request.POST)

    if request.method == 'POST':
        form = CoachRegistrationForm(request.POST)
        
        if form.is_valid():
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data.get('username'),
                email=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name')
            )

            # Create Coach and link it to user
            coach = form.save(commit=False)
            coach.user = user
            coach.save()

            # Log the user in and redirect
            login (request, user)
            messages.success(request, 'Successfully registered as Coach!')
            return redirect('users:show_profile')
        else:
            form = CoachRegistrationForm

    context = {'form': form}
    return render(request, 'register_coach.html', context)

# AUTHENTICATION VIEWS

def login_user(request):

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("main:show_main")
    else:
        form = AuthenticationForm(request)

    context = {'form': form}
    return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    return redirect('main:show_main')

# PROFILE VIEWS

@login_required(login_url='/login')
def show_profile(request):
    # Check if user is Member or Coach
    if hasattr(request.user, 'member'):
        profile = request.user.member
        template = 'profile_member.html'
    elif hasattr(request.user, 'coach'):
        profile = request.user.coach
        template = 'profile_coach.html'
    else: 
        # Handle cases like superuser or user without profile
        return render(request, 'main:show_main')
        
    context = {
        'user': request.user,
        'profile': profile
    }
    return render(request, template, context)

login_required(login_url='/login')
@transaction.atomic
def edit_profile(request):

    if hasattr(request.user, 'member'):
        ProfileEditForm = MemberEditForm
        profile_instance = request.user.member
    elif hasattr(request.user, 'coach'):
        ProfileEditForm = CoachEditForm
        profile_instance = request.user.coach
    else:
        # No profile to edit
        return redirect('main:show_main')

    if request.method == 'POST':
        # Create forms with submitted data
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile_instance)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:show_profile')
    else:
        # For a GET request, create the initial forms with existing data
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile_instance)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'edit_profile.html', context)

# COACH LIST 

# COACH LIST 


# MEMBER

def member_details(request, id):
    member = get_object_or_404(Member, pk=id)

    context = {
        'member': member
    }

    return render(request, "member_details.html", context)

def coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)
    context = {
        'coach': coach
    }
    return render(request, 'coach_detail.html', context)

def coach_list(request):
    coaches = Coach.objects.all()
    context = {
        'coaches': coaches
    }
    return render(request, 'coach_list.html', context)
    

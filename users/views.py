from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
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
            return redirect("users:coach_list")
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
        template = 'users/profile_member.html'
        profile_form = MemberEditForm(instance=profile)
    elif hasattr(request.user, 'coach'):
        profile = request.user.coach
        template = 'users/profile_coach.html'
        profile_form = CoachEditForm(instance=profile)
    else:
        # Fallback for users without a profile (e.g., superuser)
        messages.info(request, "You don't have a member or coach profile.")
        return redirect('main:show_main')

    user_form = UserEditForm(instance=request.user)

    context = {
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
    }

    # You need to decide which template to render here.
    # Assuming you want to show the modal on the user's profile page.
    if hasattr(request.user, 'member'):
        template = 'profile_member.html'
        profile = request.user.member
    else:
        template = 'profile_coach.html'
        profile = request.user.coach

    context['profile'] = profile
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
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=profile_instance)
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            if is_ajax:
                profile_data = {
                    'city': profile_instance.city,
                    'phone': profile_instance.phone,
                    'description': profile_instance.description,
                    'profile_photo': profile_instance.profile_photo,
                }
                if hasattr(request.user, 'coach'):
                    profile_data['sport'] = profile_instance.get_sport_display()
                    profile_data['hourly_fee'] = profile_instance.hourly_fee

                return JsonResponse({
                    'success': True,
                    'user': {
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'email': request.user.email,
                    },
                    'profile': profile_data
                })

            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:show_profile')

    else:
        # For a GET request, create the initial forms with existing data
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile_instance)

    # This context will be used for GET requests and invalid non-AJAX POSTs
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    # This will render the profile page with the forms
    # You need to decide which template to render here.
    # Assuming you want to show the modal on the user's profile page.
    if hasattr(request.user, 'member'):
        template = 'profile_member.html'
        profile = request.user.member
    else:
        template = 'profile_coach.html'
        profile = request.user.coach

    context['profile'] = profile
    return render(request, f'users/{template}', context)

# Details (Able to be viewed by all user)

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
    

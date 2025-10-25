from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import Member, Coach
from .forms import (
    MemberRegistrationForm,
    CoachRegistrationForm,
    UserEditForm,
    MemberEditForm,
    CoachEditForm
)
from booking.models import Booking


# =========================
# AUTH / REGISTRATION
# =========================

@transaction.atomic
def register_member(request):
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )
            member = form.save(commit=False)
            member.user = user
            member.save()

            login(request, user)
            messages.success(request, 'Successfully registered as Member!')
            return redirect('users:show_profile')
    else:
        form = MemberRegistrationForm()

    return render(request, 'register_member.html', {'form': form})


@transaction.atomic
def register_coach(request):
    if request.method == 'POST':
        form = CoachRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', '')
            )
            coach = form.save(commit=False)
            coach.user = user
            coach.save()

            login(request, user)
            messages.success(request, 'Successfully registered as Coach!')
            return redirect('users:show_profile')
    else:
        form = CoachRegistrationForm()

    return render(request, 'register_coach.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("users:coach_list")
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('main:show_main')


# =========================
# PROFILE
# =========================

@login_required(login_url='/account/login/')
def show_profile(request):
    user = request.user
    context = {'user': user}
    bookings = None
    today = timezone.now().date()

    if hasattr(user, 'member'):
        profile = user.member
        bookings = Booking.objects.filter(member=user.member).order_by('-date', '-start_time')
        context.update({
            'profile': profile,
            'bookings': bookings,
            'today': today,
        })
        return render(request, 'profile_member.html', context)
    
    elif hasattr(user, 'coach'):
        profile = user.coach
        bookings = Booking.objects.filter(coach=user.coach).order_by('-date', '-start_time')
        context.update({
            'profile': profile,
            'bookings': bookings,
            'today': today,
        })
        return render(request, 'profile_coach.html', context)
    
    return redirect('main:show_main')


@login_required(login_url='/login')
@transaction.atomic
def edit_profile(request):
    """
    Edit profil untuk Member / Coach.
    Support AJAX (kembalikan JSON) & non-AJAX (redirect + messages).
    """
    if hasattr(request.user, 'member'):
        ProfileEditForm = MemberEditForm
        profile_instance = request.user.member
        template = 'users/profile_member.html'
    elif hasattr(request.user, 'coach'):
        ProfileEditForm = CoachEditForm
        profile_instance = request.user.coach
        template = 'users/profile_coach.html'
    else:
        return redirect('main:show_main')

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=profile_instance)
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            if is_ajax:
                profile_data = {
                    'city': getattr(profile_instance, 'city', ''),
                    'phone': getattr(profile_instance, 'phone', ''),
                    'description': getattr(profile_instance, 'description', ''),
                    'profile_photo': getattr(profile_instance, 'profile_photo', ''),
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
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile_instance)

    # This context will be used for GET requests and invalid non-AJAX POSTs
    context = {
        'profile': profile_instance,
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
    return render(request, "member_details.html", {'member': member})


def coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)
    return render(request, 'coach_detail.html', {'coach': coach})


def coach_list(request):
    coaches = Coach.objects.all()
    context = {
        'coaches': coaches
    }
    return render(request, 'coach_list.html', context)
    
def coach_list(request):
    query = request.GET.get('q', '')
    coaches = Coach.objects.all()

    if query:
        coaches = coaches.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(sport__icontains=query) |
            Q(city__icontains=query)
        ).distinct()

    context = {
        'coaches': coaches,
        'search_query': query,
    }
    return render(request, 'coach_list.html', context)
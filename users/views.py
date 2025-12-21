from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt

import requests,json

from .models import Member, Coach
from .forms import (
    MemberRegistrationForm,
    CoachRegistrationForm,
    UserEditForm,
    MemberEditForm,
    CoachEditForm
)
from booking.models import Booking

DEFAULT_AVATAR = "https://icon-library.com/images/default-profile-icon/default-profile-icon-24.jpg"

# AUTH / REGISTRATION

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

# PROFILE

@login_required(login_url='/account/login/')
def show_profile(request):
    user = request.user
    context = {'user': user}
    bookings = None
    today = timezone.now().date()

    if hasattr(user, 'member'):
        profile = user.member
        bookings = Booking.objects.filter(member=user.member).order_by('-date', '-start_time')
        user_form = UserEditForm(instance=user)
        profile_form = MemberEditForm(instance=profile)
        context.update({
            'profile': profile,
            'bookings': bookings,
            'today': today,
            'user_form': user_form,
            'profile_form': profile_form,
        })
        return render(request, 'profile_member.html', context)
    
    elif hasattr(user, 'coach'):
        profile = user.coach
        bookings = Booking.objects.filter(coach=user.coach).order_by('-date', '-start_time')
        user_form = UserEditForm(instance=user)
        profile_form = CoachEditForm(instance=profile)
        context.update({
            'profile': profile,
            'bookings': bookings,
            'today': today,
            'user_form': user_form,
            'profile_form': profile_form,
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
    if hasattr(request.user, 'member'):
        template = 'profile_member.html'
        profile = request.user.member
    else:
        template = 'profile_coach.html'
        profile = request.user.coach

    context['profile'] = profile
    return render(request, f'users/{template}', context)

# DETAILS (Able to be viewed by all user)

def member_details(request, id):
    member = get_object_or_404(Member, pk=id)
    return render(request, "member_details.html", {'member': member})


def coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)
    return render(request, 'coach_detail.html', {'coach': coach})
    
def coach_list(request):
    query = request.GET.get('q', '')
    sport_filter = request.GET.get('sport', '')
    
    coaches = Coach.objects.all()

    # Search filter
    if query:
        coaches = coaches.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(sport__icontains=query) |
            Q(city__icontains=query)
        ).distinct()

    # Sport filter
    if sport_filter:
        coaches = coaches.filter(sport=sport_filter)

    # Get sport choices from the Coach model
    sport_choices = Coach._meta.get_field('sport').choices

    # Pagination - 12 coaches per page
    paginator = Paginator(coaches, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'coaches': page_obj,
        'search_query': query,
        'sport_filter': sport_filter,
        'sport_choices': sport_choices,
        'page_obj': page_obj,
    }
    return render(request, 'coach_list.html', context)

# FLUTTER ENDPOINTS

def coaches_json(request):
    query = request.GET.get('q', '')
    sport_filter = request.GET.get('sport', '')

    coaches = Coach.objects.select_related('user').all()

    # Search Filtering
    if query:
        coaches = coaches.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(sport__icontains=query) |
            Q(city__icontains=query)
        ).distinct()

    # Sport Category Filtering
    if sport_filter:
        coaches = coaches.filter(sport=sport_filter)

    # Serialize Coaches Data
    data = []
    for coach in coaches:
        data.append({
            'id': str(coach.id),
            'username': coach.user.username,
            'full_name': coach.user.get_full_name(),
            'sport': coach.sport,
            'city': coach.city,
            'hourly_fee': int(coach.hourly_fee) if coach.hourly_fee else 0,
            'description': coach.description or "",
            'profile_photo': coach.profile_photo or DEFAULT_AVATAR,
        })
    
    return JsonResponse(data, safe=False)

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)
    
@csrf_exempt
def logout_flutter(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse({"status": True, "message": "Successfully logged out."}, status=200)
        else:
            return JsonResponse({"status": False, "message": "User not authenticated."}, status=401)
    return JsonResponse({"status": False, "message": "Invalid request method."}, status=400)

@csrf_exempt
@login_required
@transaction.atomic
def edit_profile_flutter(request):
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update User Model
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()

        # Update Profile Model (Coach or Member)
        profile_data = {}
        if hasattr(user, 'coach'):
            profile = user.coach
            profile.city = data.get('city', profile.city)
            profile.phone = data.get('phone', profile.phone)
            profile.description = data.get('description', profile.description)
            profile.profile_photo = data.get('profile_photo', profile.profile_photo)
            profile.sport = data.get('sport', profile.sport)
            profile.hourly_fee = data.get('hourly_fee', profile.hourly_fee)
            profile.save()
            
            profile_data = {
                'sport': profile.sport,
                'sport_display': profile.get_sport_display(),
                'hourly_fee': int(profile.hourly_fee),
            }

        elif hasattr(user, 'member'):
            profile = user.member
            profile.city = data.get('city', profile.city)
            profile.phone = data.get('phone', profile.phone)
            profile.description = data.get('description', profile.description)
            profile.profile_photo = data.get('profile_photo', profile.profile_photo)
            profile.save()

        # Prepare Response
        base_profile_data = {
            'city': profile.city,
            'phone': profile.phone,
            'description': profile.description or "",
            'profile_photo': profile.profile_photo or "",
        }
        profile_data.update(base_profile_data)

        return JsonResponse({
            'status': True,
            'message': 'Profile updated successfully!',
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            },
            'profile': profile_data
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': False, 'message': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': False, 'message': f'An error occurred: {str(e)}'}, status=500)
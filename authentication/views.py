from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
import json

@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return JsonResponse({
                "status": False,
                "message": "Username and password are required."
            }, status=400)

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)

                # Determine role & fetch profile data
                role = "member"
                profile_data = {}

                try:
                    if hasattr(user, 'coach'):
                        role = "coach"
                        coach = user.coach
                        profile_data = {
                            "id": str(coach.id),
                            "city": coach.city,
                            "phone": coach.phone,
                            "description": coach.description,
                            "profile_photo": coach.profile_photo,
                            "sport": coach.sport,
                            "hourly_fee": coach.hourly_fee,
                        }
                    elif hasattr(user, 'member'):
                        role = "member"
                        member = user.member
                        profile_data = {
                            "id": str(member.id),
                            "city": member.city,
                            "phone": member.phone,
                            "description": member.description,
                            "profile_photo": member.profile_photo,
                        }
                except Exception as e:
                    print(f"Error fetching profile: {e}")
                    # Tetap lanjut login meski profil gagal load, tapi profile kosong

                return JsonResponse({
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "status": True,
                    "message": "Login successful!",
                    "role": role,
                    "profile": profile_data  # Data ini yang ditunggu Flutter
                }, status=200)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Login failed, account is disabled."
                }, status=401)
        else:
            return JsonResponse({
                "status": False,
                "message": "Login failed, please check your username or password."
            }, status=401)
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method. Use POST."
        }, status=405)
@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON format."
            }, status=400)
        
        username = data.get('username', '').strip()
        password1 = data.get('password1', '').strip()
        password2 = data.get('password2', '').strip()
        role = data.get('role', 'member')
        
        # Get additional fields
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        city = data.get('city', '').strip()
        phone = data.get('phone', '').strip()
        
        # Validation
        if not username:
            return JsonResponse({
                "status": False,
                "message": "Username is required."
            }, status=400)
        
        if not password1 or not password2:
            return JsonResponse({
                "status": False,
                "message": "Password is required."
            }, status=400)
        
        if password1 != password2:
            return JsonResponse({
                "status": False,
                "message": "Passwords do not match."
            }, status=400)
        
        if len(password1) < 6:
            return JsonResponse({
                "status": False,
                "message": "Password must be at least 6 characters long."
            }, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "status": False,
                "message": "Username already exists."
            }, status=400)
        
        if email and User.objects.filter(email=email).exists():
            return JsonResponse({
                "status": False,
                "message": "Email already exists."
            }, status=400)
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            user.save()
            
            # Create role-specific profile
            if role == 'coach':
                try:
                    from users.models import Coach
                    sport = data.get('sport', 'other')
                    hourly_fee = data.get('hourly_fee', 0)
                    Coach.objects.create(
                        user=user,
                        city=city,
                        phone=phone,
                        sport=sport,
                        hourly_fee=hourly_fee
                    )
                except Exception as e:
                    return JsonResponse({
                        "status": False,
                        "message": f"Error creating coach profile: {str(e)}"
                    }, status=500)
            else:
                try:
                    from users.models import Member
                    Member.objects.create(
                        user=user,
                        city=city,
                        phone=phone
                    )
                except Exception as e:
                    return JsonResponse({
                        "status": False,
                        "message": f"Error creating member profile: {str(e)}"
                    }, status=500)
            
            return JsonResponse({
                "username": user.username,
                "status": 'success',
                "message": "User created successfully!",
                "role": role
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error creating user: {str(e)}"
            }, status=500)
    
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method. Use POST."
        }, status=405)

@csrf_exempt
def logout(request):
    try:
        username = request.user.username if request.user.is_authenticated else "User"
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logged out successfully!"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": False,
            "message": f"Logout failed: {str(e)}"
        }, status=401)
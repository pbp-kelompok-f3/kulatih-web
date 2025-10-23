from django.urls import path
from .views import *

app_name = 'users'

urlpatterns = [
    # Registration
    path('register/member/', register_member, name='register_member'),
    path('register/coach/', register_coach, name='register_coach'),
    
    # Authentication
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    
    # Profile
    path('profile/', show_profile, name='show_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    # Coach
    

    # Member
    path('member/<uuid:id>', member_details, name='member_details')
]
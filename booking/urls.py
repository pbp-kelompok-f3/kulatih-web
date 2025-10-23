# bookings/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.booking_list, name='list'),                      
    path('create/', views.create_booking, name='create'),           
    path('<int:booking_id>/edit/', views.edit_booking, name='edit'),
    path('<int:booking_id>/cancel/', views.cancel_booking, name='cancel'),  
    path('<int:booking_id>/reschedule/', views.reschedule_booking, name='reschedule'),  
]

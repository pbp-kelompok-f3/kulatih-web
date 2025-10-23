# bookings/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.booking_list, name='list'),
    path('api/upcoming/', views.api_upcoming, name='api_upcoming'),
    path('api/history/',  views.api_history,  name='api_history'),
    path('ajax/cancel/<int:booking_id>/',     views.ajax_cancel,     name='ajax_cancel'),
    path('ajax/reschedule/<int:booking_id>/', views.ajax_reschedule, name='ajax_reschedule'),
    path('create/', views.create_booking, name='create'),
]

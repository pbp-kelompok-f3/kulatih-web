from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Main pages
    path('', views.booking_list, name='list'),
    path('create/<uuid:coach_id>/', views.create_booking, name='create'),
    path('edit/<int:booking_id>/', views.edit_booking, name='edit'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel'),
    path('reschedule/<int:booking_id>/', views.reschedule_booking, name='reschedule'),

    # AJAX Member actions
    path('ajax_cancel/<int:booking_id>/', views.ajax_cancel, name='ajax_cancel'),
    path('ajax_reschedule/<int:booking_id>/', views.ajax_reschedule, name='ajax_reschedule'),

    # AJAX Coach actions
    path('ajax_accept_reschedule/<int:booking_id>/', views.ajax_accept_reschedule, name='ajax_accept_reschedule'),
    path('ajax_reject_reschedule/<int:booking_id>/', views.ajax_reject_reschedule, name='ajax_reject_reschedule'),
    path('ajax_confirm_booking/<int:booking_id>/', views.ajax_confirm_booking, name='ajax_confirm_booking'),
    
    # API for Flutter
    path('api/list/', views.api_booking_list, name='api_booking_list'),
    path('api/create/', views.api_create_booking, name='api_create_booking'),
    path('api/cancel/<int:booking_id>/', views.api_cancel_booking, name='api_cancel_booking'),
    path('api/reschedule/<int:booking_id>/', views.api_reschedule_booking, name='api_reschedule_booking'),

]
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.booking_list, name='list'),
    path('create/', views.create_booking, name='create'),
    path('edit/<int:booking_id>/', views.edit_booking, name='edit'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel'),
    path('reschedule/<int:booking_id>/', views.reschedule_booking, name='reschedule'),

    # AJAX & API
    path('ajax/cancel/<int:booking_id>/', views.ajax_cancel, name='ajax_cancel'),
    path('ajax/reschedule/<int:booking_id>/', views.ajax_reschedule, name='ajax_reschedule'),
]

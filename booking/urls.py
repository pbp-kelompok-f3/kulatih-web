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
    path('json/list/', views.booking_list_json, name='list_json'),
    path('json/<uuid:coach_id>/create/', views.create_booking_json, name='create_json'),
    path('json/<int:booking_id>/edit/', views.edit_booking_json, name='edit_json'),
    path('json/<int:booking_id>/cancel/', views.cancel_booking_json, name='cancel_json'),
    path('json/<int:booking_id>/reschedule/', views.reschedule_json, name='reschedule_json'),
    path('json/<int:booking_id>/confirm/', views.confirm_booking_json, name='confirm_json'),
    path('json/<int:booking_id>/accept/', views.accept_reschedule_json, name='accept_json'),
    path('json/<int:booking_id>/reject/', views.reject_reschedule_json, name='reject_json'),
]
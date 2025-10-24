from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_home, name='home'),
    path('<int:id>/', views.community_detail, name='detail'),
    path('create/', views.community_create, name='create'),
    path('join/<int:id>/', views.join_community, name='join'),
    path('leave/<int:id>/', views.leave_community, name='leave'),
    path('my/', views.my_community_list, name='my_list'),
    path('my/<int:id>/', views.my_community_group, name='my_group'),

    # AJAX untuk message 
    path('my/<int:id>/message/<int:msg_id>/edit/', views.edit_message, name='edit_message'),
    path('my/<int:id>/message/<int:msg_id>/delete/', views.delete_message, name='delete_message'),
    path('my/<int:id>/send_message_ajax/', views.send_message_ajax, name='send_message_ajax'),
]

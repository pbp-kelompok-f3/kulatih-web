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
    path('json/', views.communities_json, name='communities_json'),
    path('<int:id>/json/', views.community_detail_json, name='community_detail_json'),
    path('my/<int:id>/messages/json/', views.community_messages_json, name='community_messages_json'),
    path('join/<int:id>/json/', views.join_community_json, name='join_community_json'),
    path('leave/<int:id>/json/', views.leave_community_json, name='leave_community_json'),
    path('json/create', views.community_create_json, name='community_create_json'),
    path('my/<int:id>/json/edit_message/<int:msg_id>/', views.edit_message_json, name='edit_message_json'),
    path('my/<int:id>/json/delete_message/<int:msg_id>/', views.delete_message_json, name='delete_message_json'), 
    path("my/json/", views.my_community_list_json, name="my_community_list_json"),
    path('my/<int:id>/json/send_message/', views.my_community_group_json, name='send_message_json'),
    path('my/<int:id>/send_message_ajax/', views.send_message_ajax, name='send_message_ajax'),
    path('proxy-image/', views.proxy_image, name='proxy_image'),
]

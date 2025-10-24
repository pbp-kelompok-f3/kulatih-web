from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
<<<<<<< HEAD
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
=======
    path('', views.community_home, name='home'),                          # Community (main page)
    path('make/', views.community_create, name='create'),                 # Create community (form)
    path('<slug:slug>/', views.community_detail, name='detail'),          # Community detail
    path('<slug:slug>/join/', views.join_community, name='join'),         # Join
    path('my/', views.my_community_list, name='my_list'),                 # My community list
    path('my/<slug:slug>/', views.my_community_group, name='my_group'),   # My community group (chat)
    path('my/<slug:slug>/leave/', views.leave_community, name='leave'),   # Leave
>>>>>>> forum-modul-izzati
]

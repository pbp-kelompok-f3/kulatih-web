from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_home, name='home'),                          # Community (main page)
    path('make/', views.community_create, name='create'),                 # Create community (form)
    path('<slug:slug>/', views.community_detail, name='detail'),          # Community detail
    path('<slug:slug>/join/', views.join_community, name='join'),         # Join
    path('my/', views.my_community_list, name='my_list'),                 # My community list
    path('my/<slug:slug>/', views.my_community_group, name='my_group'),   # My community group (chat)
    path('my/<slug:slug>/leave/', views.leave_community, name='leave'),   # Leave
]

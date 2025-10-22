from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('new/', views.create_post, name='create_post'),
    path('<int:post_id>/like/', views.like_post, name='like_post'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/delete/<int:post_id>/', views.delete_post, name='delete_post'),
]

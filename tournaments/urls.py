from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path('', views.tournament_view, name='tournament_view'),
    path('create/', views.create_tournament, name='create_tournament'),
    path('delete/<uuid:tournament_id>/', views.delete_tournament, name='delete_tournament'),
    path('assign/<uuid:tournament_id>/', views.assign_tournament, name='assign_tournament'),
    path('<uuid:tournament_id>/', views.tournament_show, name='tournament_show'),
    path('<uuid:tournament_id>/edit-ajax/', views.edit_tournament_ajax, name='edit_tournament_ajax'),
    path('my/', views.my_tournaments_ajax, name='my_tournaments_ajax'),

]

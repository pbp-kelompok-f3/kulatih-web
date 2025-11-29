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
    path('json/tournaments/', views.tournament_view_flutter, name='tournament_view_json'),
    path('json/tournaments/my/', views.my_tournaments_flutter, name='my_tournaments_flutter'),
    path('json/tournaments/create/', views.create_tournament_flutter, name='create_tournament_flutter'),
    path('json/tournaments/<uuid:tournament_id>/edit/', views.edit_tournament_flutter, name='edit_tournament_flutter'),
    path('json/tournaments/<uuid:tournament_id>/delete/', views.delete_tournament_flutter, name='delete_tournament_flutter'),
    
]

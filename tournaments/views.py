from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Tournament
from users.models import Coach, Member 
from .forms import TournamentForm
import json

@login_required
def tournaments_view(request):
    tournaments = Tournament.objects.all()
    return render(request, 'tournament/tournaments.html', {'tournaments': tournaments})

@login_required
@csrf_exempt
def create_tournament(request):
    if request.method == "POST":
        if not hasattr(request.user, 'coach_profile'):
            return JsonResponse({'error': 'Hanya coach yang bisa membuat tournament'}, status=403)

        data = json.loads(request.body)
        form = TournamentForm(data)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.pembuatTournaments = request.user.coach_profile
            tournament.save()
            return JsonResponse({'message': 'Tournament berhasil dibuat!', 'id': str(tournament.idTournaments)})
        else:
            return JsonResponse({'error': form.errors}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@csrf_exempt
def delete_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)
    if request.user.coach_profile != tournament.pembuatTournaments:
        return JsonResponse({'error': 'Kamu tidak berhak menghapus tournament ini'}, status=403)
    
    tournament.delete()
    return JsonResponse({'message': 'Tournament berhasil dihapus!'})

@login_required
@csrf_exempt
def assign_tournament(request, tournament_id):
    if request.method == "POST":
        tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

        if not hasattr(request.user, 'customer_profile'):
            return JsonResponse({'error': 'Hanya customer yang bisa daftar'}, status=403)

        customer = request.user.customer_profile
        tournament.pesertaTournaments.add(customer)
        return JsonResponse({'message': f'{customer.user.username} berhasil daftar ke {tournament.namaTournaments}!'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

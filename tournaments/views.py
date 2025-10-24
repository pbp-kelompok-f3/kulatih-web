from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Tournament
from users.models import Coach, Member
from .forms import TournamentForm
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def tournament_view(request):
    tournaments = Tournament.objects.all()
    is_coach = hasattr(request.user, 'coach')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = []
        for t in tournaments:
            pembuat_username = (
                t.pembuatTournaments.user.username
                if hasattr(t.pembuatTournaments, 'user')
                else "Unknown"
            )
            data.append({
                'id': str(t.idTournaments),
                'nama': t.namaTournaments,
                'tipe': t.tipeTournaments,
                'tanggal': t.tanggalTournaments.strftime('%Y-%m-%d'),
                'lokasi': t.lokasiTournaments,
                'poster': t.posterTournaments.url if t.posterTournaments else '/static/images/empty.png',
                'deskripsi': t.deskripsiTournaments,
                'pembuat': pembuat_username,
            })
        return JsonResponse({'tournaments': data})

    return render(request, 'tournament_list.html', {
        'tournaments': tournaments,
        'is_coach': is_coach
    })



def tournament_show(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    pembuat_username = (
        tournament.pembuatTournaments.user.username
        if hasattr(tournament.pembuatTournaments, 'user')
        else "Unknown"
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'id': str(tournament.idTournaments),
            'nama': tournament.namaTournaments,
            'tipe': tournament.tipeTournaments,
            'tanggal': tournament.tanggalTournaments.strftime('%Y-%m-%d'),
            'lokasi': tournament.lokasiTournaments,
            'poster': tournament.posterTournaments,
            'deskripsi': tournament.deskripsiTournaments,
            'pembuat': pembuat_username,
        }
        return JsonResponse({'tournament': data})

    return render(request, 'tournament_show.html', {'tournament': tournament})


@csrf_exempt
@login_required
def create_tournament(request):
    is_coach = hasattr(request.user, 'coach')

    if not is_coach:
        return render(request, 'tournament_create.html', {'is_coach': False})

    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.pembuatTournaments = request.user.coach
            tournament.save()
            return redirect('tournaments:tournament_view')
    else:
        form = TournamentForm()

    return render(request, 'tournament_create.html', {'form': form, 'is_coach': True})


@csrf_exempt
def delete_tournament(request, tournament_id):
    if request.method != "DELETE":
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if not hasattr(request.user, 'coach') or request.user.coach != tournament.pembuatTournaments:
        return JsonResponse({'error': 'Kamu tidak berhak menghapus tournament ini'}, status=403)
    
    tournament.delete()
    return JsonResponse({'message': 'Tournament berhasil dihapus!'})


@login_required
@csrf_exempt
def assign_tournament(request, tournament_id):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if not hasattr(request.user, 'member'):
        return JsonResponse({'error': 'Hanya member yang bisa daftar'}, status=403)

    member = request.user.member

    if tournament.pesertaTournaments.filter(pk=member.pk).exists():
        return JsonResponse({'error': 'Kamu sudah terdaftar di turnamen ini'}, status=400)

    tournament.pesertaTournaments.add(member)
    return JsonResponse({'message': f'{member.user.username} berhasil daftar ke {tournament.namaTournaments}!'})


def dummy_home(request):
    return render(request, "dummy_home.html")
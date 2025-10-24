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
                'tanggal': t.tanggalTournaments.strftime('%b %d, %Y'),
                'lokasi': t.lokasiTournaments,
                'poster': t.posterTournaments or '/static/images/empty.png',  # 🟢 FIXED
                'deskripsi': t.deskripsiTournaments,
                'pembuat': pembuat_username,
            })
        return JsonResponse({'tournaments': data})

    return render(request, 'tournament_list.html', {
        'tournaments': tournaments,
        'is_coach': is_coach
    })


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Tournament

@login_required
def my_tournaments_ajax(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.user

        if hasattr(user, 'coach'):
            tournaments = Tournament.objects.filter(pembuatTournaments=user.coach)
        elif hasattr(user, 'member'):
            tournaments = Tournament.objects.filter(pesertaTournaments=user.member)
        else:
            tournaments = Tournament.objects.none()

        data = []
        for t in tournaments:
            data.append({
                'id': str(t.idTournaments),
                'nama': t.namaTournaments,
                'tipe': t.tipeTournaments,
                'tanggal': t.tanggalTournaments.strftime('%Y-%m-%d'),
                'lokasi': t.lokasiTournaments,
                'poster': t.posterTournaments if hasattr(t, 'posterTournaments') else '',
                'pembuat': t.pembuatTournaments.user.username,
            })

        return JsonResponse({'tournaments': data})

    return JsonResponse({'error': 'Invalid request'}, status=400)






@login_required
def tournament_show(request, tournament_id):
    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    pembuat_username = (
        tournament.pembuatTournaments.user.username
        if hasattr(tournament.pembuatTournaments, 'user')
        else "Unknown"
    )
    is_coach = hasattr(request.user, 'coach')
    is_member = hasattr(request.user, 'member')

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

    return render(request, 'tournament_show.html', {
        'tournament': tournament,
        'is_coach': is_coach,
        'is_member': is_member,
    })



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
@login_required

def delete_tournament(request, tournament_id):
    if request.method not in ["POST", "DELETE"]:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)
    if not hasattr(request.user, 'coach') or request.user.coach != tournament.pembuatTournaments:
        return JsonResponse({'error': 'Kamu tidak berhak menghapus tournament ini'}, status=403)

    tournament.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'message': 'Tournament berhasil dihapus!'})

    return redirect('tournaments:tournament_view')

@csrf_exempt
@login_required
def assign_tournament(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if not hasattr(request.user, 'member'):
        return JsonResponse({'error': 'Hanya member yang dapat mendaftar ke turnamen.'}, status=403)

    member = request.user.member

    if not tournament.flagTournaments:
        return JsonResponse({'error': 'Pendaftaran turnamen ini sudah ditutup.'}, status=400)

    if tournament.pesertaTournaments.filter(pk=member.pk).exists():
        return JsonResponse({'message': 'Anda sudah terdaftar di turnamen ini!'}, status=200)
    tournament.pesertaTournaments.add(member)
    tournament.save()

    return JsonResponse({'message': f'{member.user.username} berhasil daftar ke {tournament.namaTournaments}!'}, status=200)




@login_required
@csrf_exempt
def edit_tournament_ajax(request, tournament_id):
    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if request.method == "GET":
        return JsonResponse({
            "namaTournaments": tournament.namaTournaments,
            "lokasiTournaments": tournament.lokasiTournaments,
            "tanggalTournaments": str(tournament.tanggalTournaments),
            "deskripsiTournaments": tournament.deskripsiTournaments,
            "posterTournaments": tournament.posterTournaments,
        })

    elif request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        tournament.namaTournaments = data.get("namaTournaments", tournament.namaTournaments)
        tournament.lokasiTournaments = data.get("lokasiTournaments", tournament.lokasiTournaments)
        tournament.tanggalTournaments = data.get("tanggalTournaments", tournament.tanggalTournaments)
        tournament.deskripsiTournaments = data.get("deskripsiTournaments", tournament.deskripsiTournaments)
        tournament.posterTournaments = data.get("posterTournaments", tournament.posterTournaments)
        tournament.save()
        return JsonResponse({"message": "Tournament updated successfully!"})
    
    return JsonResponse({"error": "Invalid request method"}, status=405)
    
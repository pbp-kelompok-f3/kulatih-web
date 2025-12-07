from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
import json
from datetime import datetime
from .models import Tournament
from users.models import Coach, Member
from .forms import TournamentForm


def tournament_view(request):
    tournaments = Tournament.objects.filter(flagTournaments=True)
    if hasattr(request.user, 'coach'):
        request.session['role'] = 'coach'
    elif hasattr(request.user, 'member'):
        request.session['role'] = 'member'
    else:
        request.session['role'] = 'guest'

    is_coach = request.session.get('role') == 'coach'

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
                'poster': t.posterTournaments or '/static/images/empty.png',
                'deskripsi': t.deskripsiTournaments,
                'pembuat': pembuat_username,
            })
        return JsonResponse({'tournaments': data})

    return render(request, 'tournament_list.html', {
        'tournaments': tournaments,
        'is_coach': is_coach,
    })



@login_required(login_url=reverse_lazy('users:login'))
def my_tournaments_ajax(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.user

        if hasattr(user, 'coach'):
            tournaments = Tournament.objects.filter(
                pembuatTournaments=user.coach,
                flagTournaments=True
            )
        elif hasattr(user, 'member'):
            tournaments = Tournament.objects.filter(
                pesertaTournaments=user.member,
                flagTournaments=True
            )
        else:
            tournaments = Tournament.objects.none()

        data = []
        for t in tournaments:
            data.append({
                'id': str(t.idTournaments),
                'nama': t.namaTournaments,
                'tipe': t.tipeTournaments,
                'tanggal': t.tanggalTournaments.strftime('%b %d, %Y'),
                'lokasi': t.lokasiTournaments,
                'poster': t.posterTournaments if hasattr(t, 'posterTournaments') else '',
                'pembuat': t.pembuatTournaments.user.username,
            })

        return JsonResponse({'tournaments': data})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url=reverse_lazy('users:login'))
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
@login_required(login_url=reverse_lazy('users:login'))
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

@login_required(login_url=reverse_lazy('users:login'))
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
@login_required(login_url=reverse_lazy('users:login'))
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


@login_required(login_url=reverse_lazy('users:login'))
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
        try:
            data = json.loads(request.body.decode("utf-8"))

            tournament.namaTournaments = data.get("namaTournaments", tournament.namaTournaments)
            tournament.lokasiTournaments = data.get("lokasiTournaments", tournament.lokasiTournaments)
            tournament.deskripsiTournaments = data.get("deskripsiTournaments", tournament.deskripsiTournaments)
            tournament.posterTournaments = data.get("posterTournaments", tournament.posterTournaments)
            tanggal_str = data.get("tanggalTournaments")
            if tanggal_str:
                try:
                    tournament.tanggalTournaments = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
                except ValueError:
                    return JsonResponse({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD."}, status=400)

            tournament.save()
            return JsonResponse({"message": "Tournament updated successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def tournament_view_flutter(request):
    tournaments = Tournament.objects.filter(flagTournaments=True)
    if hasattr(request.user, 'coach'):
        role = "coach"
    elif hasattr(request.user, 'member'):
        role = "member"
    else:
        role = "guest"

    result = []
    for t in tournaments:
        pembuat_username = (
            t.pembuatTournaments.user.username
            if hasattr(t.pembuatTournaments, 'user')
            else "Unknown"
        )

        result.append({
            "id": str(t.idTournaments),
            "nama": t.namaTournaments,
            "tipe": t.tipeTournaments,
            "tanggal": t.tanggalTournaments.strftime("%Y-%m-%d"),
            "lokasi": t.lokasiTournaments,
            "poster": t.posterTournaments or "/static/images/empty.png",
            "deskripsi": t.deskripsiTournaments,
            "pembuat": pembuat_username,
        })

    return JsonResponse({
        "role": role,
        "tournaments": result
    }, status=200)

def my_tournaments_flutter(request):
    user = request.user

    if hasattr(user, 'coach'):
        tournaments = Tournament.objects.filter(
            pembuatTournaments=user.coach,
            flagTournaments=True
        )
        role = "coach"

    elif hasattr(user, 'member'):
        tournaments = Tournament.objects.filter(
            pesertaTournaments=user.member,
            flagTournaments=True
        )
        role = "member"

    else:
        return JsonResponse({
            "error": "User tidak memiliki role coach atau member."
        }, status=403)

    data = []
    for t in tournaments:
        data.append({
            "id": str(t.idTournaments),
            "nama": t.namaTournaments,
            "tipe": t.tipeTournaments,
            "tanggal": t.tanggalTournaments.strftime("%Y-%m-%d"),
            "lokasi": t.lokasiTournaments,
            "poster": t.posterTournaments or "/static/images/empty.png",
            "pembuat": t.pembuatTournaments.user.username,
        })

    return JsonResponse({
        "role": role,
        "tournaments": data
    }, status=200)

@csrf_exempt
@login_required(login_url=reverse_lazy('users:login'))
def create_tournament_flutter(request):
    if not hasattr(request.user, 'coach'):
        return JsonResponse({"error": "Hanya coach yang dapat membuat turnamen."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Gunakan request POST."}, status=405)

    try:
        data = request.POST
        poster = request.FILES.get("posterTournaments")

        tournament = Tournament(
            namaTournaments=data.get("namaTournaments"),
            tipeTournaments=data.get("tipeTournaments"),
            tanggalTournaments=data.get("tanggalTournaments"),
            lokasiTournaments=data.get("lokasiTournaments"),
            deskripsiTournaments=data.get("deskripsiTournaments"),
            posterTournaments=poster,
            pembuatTournaments=request.user.coach
        )

        tournament.save()

        return JsonResponse({
            "message": "Tournament berhasil dibuat!",
            "id": str(tournament.idTournaments)
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@csrf_exempt
@login_required(login_url=reverse_lazy('users:login'))
def create_tournament_flutter(request):
    if not hasattr(request.user, 'coach'):
        return JsonResponse({"error": "Hanya coach yang dapat membuat turnamen."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Gunakan request POST."}, status=405)

    try:
        data = request.POST
        poster = request.FILES.get("posterTournaments")

        tournament = Tournament(
            namaTournaments=data.get("namaTournaments"),
            tipeTournaments=data.get("tipeTournaments"),
            tanggalTournaments=data.get("tanggalTournaments"),
            lokasiTournaments=data.get("lokasiTournaments"),
            deskripsiTournaments=data.get("deskripsiTournaments"),
            posterTournaments=poster,
            pembuatTournaments=request.user.coach
        )

        tournament.save()

        return JsonResponse({
            "message": "Tournament berhasil dibuat!",
            "id": str(tournament.idTournaments)
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required(login_url=reverse_lazy('users:login'))
def edit_tournament_flutter(request, tournament_id):
    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if not hasattr(request.user, 'coach') or request.user.coach != tournament.pembuatTournaments:
        return JsonResponse({"error": "Tidak punya akses untuk edit turnamen ini."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Gunakan request POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        tournament.namaTournaments = data.get("namaTournaments", tournament.namaTournaments)
        tournament.lokasiTournaments = data.get("lokasiTournaments", tournament.lokasiTournaments)
        tournament.deskripsiTournaments = data.get("deskripsiTournaments", tournament.deskripsiTournaments)

        tanggal = data.get("tanggalTournaments")
        if tanggal:
            tournament.tanggalTournaments = datetime.strptime(tanggal, "%Y-%m-%d").date()

        tournament.save()

        return JsonResponse({"message": "Tournament berhasil diupdate!"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required(login_url=reverse_lazy('users:login'))
def delete_tournament_flutter(request, tournament_id):
    if request.method != "POST":
        return JsonResponse({"error": "Gunakan request POST."}, status=405)

    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if not hasattr(request.user, 'coach') or request.user.coach != tournament.pembuatTournaments:
        return JsonResponse({"error": "Tidak punya akses menghapus turnamen ini."}, status=403)

    tournament.delete()

    return JsonResponse({"message": "Tournament berhasil dihapus!"}, status=200)

@csrf_exempt
@login_required(login_url=reverse_lazy('users:login'))
def assign_tournament_flutter(request, tournament_id):
    if request.method != "POST":
        return JsonResponse({"error": "Gunakan method POST."}, status=405)

    tournament = get_object_or_404(Tournament, idTournaments=tournament_id)

    if not hasattr(request.user, 'member'):
        return JsonResponse({
            "error": "Hanya member yang dapat mendaftar ke turnamen."
        }, status=403)

    member = request.user.member

    if not tournament.flagTournaments:
        return JsonResponse({
            "error": "Pendaftaran turnamen ini sudah ditutup."
        }, status=400)
    if tournament.pesertaTournaments.filter(pk=member.pk).exists():
        return JsonResponse({
            "message": "Anda sudah terdaftar dalam turnamen ini."
        }, status=200)

    tournament.pesertaTournaments.add(member)
    tournament.save()

    return JsonResponse({
        "message": f"{member.user.username} berhasil daftar ke {tournament.namaTournaments}!",
        "tournament_id": str(tournament.idTournaments),
        "member": member.user.username,
        "status": "success"
    }, status=200)



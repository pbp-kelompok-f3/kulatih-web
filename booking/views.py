from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Booking
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

@csrf_exempt
def booking_create(request):
    """Tambah booking baru, dengan validasi bentrok."""
    if request.method == 'POST':
        data = json.loads(request.body)

        user_name = data.get('user_name')
        coach_name = data.get('coach_name')
        sport_type = data.get('sport_type')
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        # Konversi string ke datetime
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except Exception:
            return JsonResponse({'error': 'Format tanggal/jam salah'}, status=400)

        # Validasi waktu
        if start_time >= end_time:
            return JsonResponse({'error': 'Waktu mulai harus lebih awal dari waktu selesai'}, status=400)

        # Cek bentrok jadwal coach
        if Booking.is_conflict(coach_name, date, start_time, end_time):
            return JsonResponse({'error': f'Coach {coach_name} sudah punya jadwal di jam tersebut'}, status=409)

        # Kalau aman → buat booking baru
        booking = Booking.objects.create(
            user_name=user_name,
            coach_name=coach_name,
            sport_type=sport_type,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status='pending'
        )
        return JsonResponse({'message': 'Booking berhasil dibuat', 'id': booking.id}, status=201)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


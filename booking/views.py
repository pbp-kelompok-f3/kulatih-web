from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from .models import Booking
from users.models import Coach, Member


# 🟢 List (main page /booking/)
def booking_list(request):
    bookings = Booking.objects.all().order_by('-date', '-start_time')
    today = timezone.localdate()  # ⬅️ tambahin ini buat pembanding di template

    # ubah path template supaya Django bisa nemuin file-nya
    # pastikan file kamu di: booking/templates/booking/booking_list.html
    return render(request, 'booking/booking_list.html', {
        'bookings': bookings,
        'today': today,  # ⬅️ dikirim ke template
    })


# 🟢 Create Booking
def create_booking(request):
    if request.method == 'POST':
        coach_ids = request.POST.getlist('coaches') or request.POST.getlist('coach')
        member_ids = request.POST.getlist('members') or request.POST.getlist('member')
        date_str = request.POST.get('date')
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')

        if not (date_str and start_str and end_str and coach_ids and member_ids):
            messages.error(request, "Lengkapi semua field.")
            return redirect('booking:list')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Format tanggal/jam tidak valid.")
            return redirect('booking:list')

        if start_time >= end_time:
            messages.error(request, "Jam mulai harus lebih kecil dari jam selesai.")
            return redirect('booking:list')

        if date < timezone.localdate():
            messages.error(request, "Tanggal tidak boleh di masa lalu.")
            return redirect('booking:list')

        coaches = list(Coach.objects.filter(id__in=coach_ids))
        for c in coaches:
            if Booking.is_conflict(c, date, start_time, end_time):
                messages.error(request, f"Jadwal bentrok dengan coach {c.name}.")
                return redirect('booking:list')

        booking = Booking.objects.create(
            date=date, start_time=start_time, end_time=end_time, status='pending'
        )
        booking.coach.set(coaches)
        booking.member.set(Member.objects.filter(id__in=member_ids))
        booking.save()

        messages.success(request, "Booking berhasil dibuat!")
        return redirect('booking:list')

    context = {
        'coaches': Coach.objects.all(),
        'members': Member.objects.all(),
    }
    return render(request, 'booking/create_booking.html', context)


# 🟢 Edit Booking
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        coach_ids = request.POST.getlist('coaches') or request.POST.getlist('coach')
        member_ids = request.POST.getlist('members') or request.POST.getlist('member')
        date_str = request.POST.get('date')
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')
        status = request.POST.get('status') or booking.status

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
        except (TypeError, ValueError):
            messages.error(request, "Format tanggal/jam tidak valid.")
            return redirect('booking:list')

        if start_time >= end_time:
            messages.error(request, "Jam mulai harus lebih kecil dari jam selesai.")
            return redirect('booking:list')

        coaches = list(Coach.objects.filter(id__in=coach_ids))
        for c in coaches:
            if Booking.is_conflict(c, date, start_time, end_time, exclude_booking_id=booking.id):
                messages.error(request, f"Jadwal bentrok dengan coach {c.name}.")
                return redirect('booking:list')

        booking.coach.set(coaches)
        booking.member.set(Member.objects.filter(id__in=member_ids))
        booking.date = date
        booking.start_time = start_time
        booking.end_time = end_time
        booking.status = status
        booking.save()

        messages.success(request, "Booking berhasil diubah!")
        return redirect('booking:list')

    context = {
        'booking': booking,
        'coaches': Coach.objects.all(),
        'members': Member.objects.all(),
    }
    return render(request, 'booking/edit_booking.html', context)


# 🟢 Cancel Booking (page)
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'cancelled'
    booking.save()
    messages.info(request, "Booking dibatalkan.")
    return redirect('booking:list')


# 🟢 Reschedule Booking (page)
def reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        date_str = request.POST.get('new_date')
        start_str = request.POST.get('new_start_time')
        end_str = request.POST.get('new_end_time')
        try:
            new_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_start = datetime.strptime(start_str, '%H:%M').time()
            new_end = datetime.strptime(end_str, '%H:%M').time()
        except (TypeError, ValueError):
            messages.error(request, "Format tanggal/jam tidak valid.")
            return redirect('booking:list')

        try:
            booking.reschedule(new_date, new_start, new_end)
            messages.success(request, "Booking berhasil direschedule!")
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('booking:list')

    return render(request, 'booking/reschedule_booking.html', {'booking': booking})


# 🟢 AJAX Cancel
@require_POST
def ajax_cancel(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)
    b.status = 'cancelled'
    b.save()
    return JsonResponse({'ok': True})


# 🟢 AJAX Reschedule
@require_POST
def ajax_reschedule(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    nd = request.POST.get('new_date')
    ns = request.POST.get('new_start_time')
    ne = request.POST.get('new_end_time')
    if not (nd and ns and ne):
        return JsonResponse({'ok': False, 'error': 'Invalid data'}, status=400)

    try:
        nd = datetime.strptime(nd, '%Y-%m-%d').date()
        ns = datetime.strptime(ns, '%H:%M').time()
        ne = datetime.strptime(ne, '%H:%M').time()
        b.reschedule(nd, ns, ne)
        return JsonResponse({'ok': True})
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

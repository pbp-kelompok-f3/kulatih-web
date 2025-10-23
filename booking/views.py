# bookings/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
from .models import Booking
from users.models import Coach, Member

# 🟢 List
def booking_list(request):
    bookings = Booking.objects.all().order_by('-date', '-start_time')
    return render(request, 'booking_list.html', {'bookings': bookings})

# 🟢 Create
def create_booking(request):
    if request.method == 'POST':
        coach_ids   = request.POST.getlist('coaches') or request.POST.getlist('coach')  # dukung name tunggal
        member_ids  = request.POST.getlist('members') or request.POST.getlist('member')
        date_str    = request.POST.get('date')
        start_str   = request.POST.get('start_time')
        end_str     = request.POST.get('end_time')

        if not (date_str and start_str and end_str and coach_ids and member_ids):
            messages.error(request, "Lengkapi semua field.")
            return redirect('booking_list')

        # parsing
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time   = datetime.strptime(end_str,   '%H:%M').time()
        except ValueError:
            messages.error(request, "Format tanggal/jam tidak valid.")
            return redirect('booking_list')

        if start_time >= end_time:
            messages.error(request, "Jam mulai harus lebih kecil dari jam selesai.")
            return redirect('booking_list')

        if date < timezone.localdate():
            messages.error(request, "Tanggal tidak boleh di masa lalu.")
            return redirect('booking_list')

        # cek bentrok untuk setiap coach
        coaches = list(Coach.objects.filter(id__in=coach_ids))
        for c in coaches:
            if Booking.is_conflict(c, date, start_time, end_time):
                messages.error(request, f"Jadwal bentrok dengan coach {c.name}.")
                return redirect('booking_list')

        booking = Booking.objects.create(
            date=date, start_time=start_time, end_time=end_time, status='pending'
        )
        booking.coach.set(coaches)
        booking.member.set(Member.objects.filter(id__in=member_ids))
        booking.save()

        messages.success(request, "Booking berhasil dibuat!")
        return redirect('booking_list')

    context = {
        'coaches': Coach.objects.all(),
        'members': Member.objects.all(),
    }
    return render(request, 'create_booking.html', context)

# 🟢 Edit
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        coach_ids  = request.POST.getlist('coaches') or request.POST.getlist('coach')
        member_ids = request.POST.getlist('members') or request.POST.getlist('member')
        date_str   = request.POST.get('date')
        start_str  = request.POST.get('start_time')
        end_str    = request.POST.get('end_time')
        status     = request.POST.get('status') or booking.status

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time   = datetime.strptime(end_str,   '%H:%M').time()
        except (TypeError, ValueError):
            messages.error(request, "Format tanggal/jam tidak valid.")
            return redirect('booking_list')

        if start_time >= end_time:
            messages.error(request, "Jam mulai harus lebih kecil dari jam selesai.")
            return redirect('booking_list')

        coaches = list(Coach.objects.filter(id__in=coach_ids))
        for c in coaches:
            if Booking.is_conflict(c, date, start_time, end_time, exclude_booking_id=booking.id):
                messages.error(request, f"Jadwal bentrok dengan coach {c.name}.")
                return redirect('booking_list')

        booking.coach.set(coaches)
        booking.member.set(Member.objects.filter(id__in=member_ids))
        booking.date = date
        booking.start_time = start_time
        booking.end_time = end_time
        booking.status = status
        booking.save()

        messages.success(request, "Booking berhasil diubah!")
        return redirect('booking_list')

    context = {
        'booking': booking,
        'coaches': Coach.objects.all(),
        'members': Member.objects.all(),
    }
    return render(request, 'edit_booking.html', context)

# 🟢 Cancel
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'cancelled'
    booking.save()
    messages.info(request, "Booking dibatalkan.")
    return redirect('booking_list')

# 🟢 Reschedule (pakai tanggal & jam baru)
def reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        date_str  = request.POST.get('new_date')
        start_str = request.POST.get('new_start_time')
        end_str   = request.POST.get('new_end_time')
        try:
            new_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_start = datetime.strptime(start_str, '%H:%M').time()
            new_end   = datetime.strptime(end_str,   '%H:%M').time()
        except (TypeError, ValueError):
            messages.error(request, "Format tanggal/jam tidak valid.")
            return redirect('booking_list')

        try:
            booking.reschedule(new_date, new_start, new_end)
            messages.success(request, "Booking berhasil direschedule!")
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('booking_list')

    return render(request, 'reschedule_booking.html', {'booking': booking})

# return HTML partial
def api_my_upcoming(request):
    ...
    html = render_to_string('bookings/_booking_cards.html', {'bookings': qs}, request=request)
    return HttpResponse(html)

def api_my_history(request):
    ...
    html = render_to_string('bookings/_booking_cards.html', {'bookings': qs}, request=request)
    return HttpResponse(html)

# actions
def ajax_cancel_booking(request, booking_id):
    if request.method != 'POST': return HttpResponseBadRequest('POST only')
    b = get_object_or_404(Booking, id=booking_id)
    b.status = 'cancelled'
    b.save(update_fields=['status'])
    return JsonResponse({'ok': True})

def ajax_reschedule_booking(request, booking_id):
    if request.method != 'POST': return HttpResponseBadRequest('POST only')
    ...
    return JsonResponse({'ok': True})

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Booking
from users.models import Coach, Member

# 🟢 Tampilkan semua booking
def booking_list(request):
    bookings = Booking.objects.all().order_by('-date')
    return render(request, 'booking_list.html', {'bookings': bookings})

# 🟢 Buat booking baru
def create_booking(request):
    if request.method == 'POST':
        coach_ids = request.POST.getlist('coaches')
        member_ids = request.POST.getlist('members')
        date = request.POST.get('date')

        booking = Booking.objects.create(date=date, status='pending')
        booking.coach.set(Coach.objects.filter(id__in=coach_ids))
        booking.member.set(Member.objects.filter(id__in=member_ids))
        booking.save()

        messages.success(request, "Booking berhasil dibuat!")
        return redirect('booking_list')

    context = {
        'coaches': Coach.objects.all(),
        'members': Member.objects.all(),
    }
    return render(request, 'create_booking.html', context)

# 🟢 Edit booking
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        coach_ids = request.POST.getlist('coaches')
        member_ids = request.POST.getlist('members')
        date = request.POST.get('date')
        status = request.POST.get('status')

        booking.coach.set(Coach.objects.filter(id__in=coach_ids))
        booking.member.set(Member.objects.filter(id__in=member_ids))
        booking.date = date
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

# 🟢 Cancel booking
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'cancelled'
    booking.save()
    messages.info(request, "Booking dibatalkan.")
    return redirect('booking_list')

# 🟢 Reschedule booking
def reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        try:
            booking.reschedule(new_date)
            messages.success(request, "Booking berhasil direschedule!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('booking_list')

    return render(request, 'reschedule_booking.html', {'booking': booking})

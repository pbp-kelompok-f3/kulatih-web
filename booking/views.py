from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Booking
from users.models import Coach, Member


# 🟢 LIST BOOKINGS
def booking_list(request):
    today = timezone.localdate()

    if not request.user.is_authenticated:
        messages.error(request, "Please log in first.")
        return redirect("/accounts/login/")

    is_coach = hasattr(request.user, "coach")
    is_member = hasattr(request.user, "member")

    # Filter sesuai role
    if is_coach:
        bookings = Booking.objects.filter(coach__in=[request.user.coach]).order_by('-date', '-start_time')
        template = "booking/booking_list_content_coach.html"
    elif is_member:
        bookings = Booking.objects.filter(member__in=[request.user.member]).order_by('-date', '-start_time')
        template = "booking/booking_list_content_user.html"
    else:
        bookings = Booking.objects.none()
        template = "booking/booking_list_content_user.html"

    context = {
        "bookings": bookings,
        "today": today,
        "is_coach": is_coach,
        "is_member": is_member,
    }
    return render(request, template, context)


# 🟢 CREATE BOOKING
def create_booking(request):
    is_member = hasattr(request.user, "member")

    if request.method == "POST":
        name = request.POST.get("name")
        location = request.POST.get("location")
        datetime_str = request.POST.get("date")

        # Validasi field
        if not (name and location and datetime_str):
            messages.error(request, "Please fill all fields.")
            return redirect("booking:create")

        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            date = dt.date()
            start_time = dt.time()
            end_time = (dt + timedelta(hours=1)).time()  # durasi 1 jam
        except ValueError:
            messages.error(request, "Invalid date/time format.")
            return redirect("booking:create")

        if date < timezone.localdate():
            messages.error(request, "Date cannot be in the past.")
            return redirect("booking:create")

        if not is_member:
            messages.error(request, "You must log in as a member to make a booking.")
            return redirect("booking:list")

        # Ambil member login
        member = request.user.member
        if name.strip() and name != member.name:
            member.name = name
            member.save()

        # Ambil coach default (sementara)
        coach = Coach.objects.first()
        if not coach:
            messages.error(request, "No coach available yet.")
            return redirect("booking:list")

        # Simpan booking
        booking = Booking.objects.create(
            date=date,
            start_time=start_time,
            end_time=end_time,
            location=location,
            status="pending",
        )
        booking.member.add(member)
        booking.coach.add(coach)
        booking.save()

        messages.success(request, f"Booking created successfully with coach {coach.name}!")
        return redirect("booking:list")

    return render(request, "booking/create_booking.html")


# 🟢 EDIT BOOKING
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
                messages.error(request, f"Jadwal bentrok dengan coach {c.user.username}.")
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


# 🟢 CANCEL BOOKING (page)
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'cancelled'
    booking.save()
    messages.info(request, "Booking dibatalkan.")
    return redirect('booking:list')


# 🟢 RESCHEDULE BOOKING (page)
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


# 🟢 AJAX CANCEL
@require_POST
def ajax_cancel(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
        b.status = "cancelled"
        b.save()
        return JsonResponse({"ok": True})
    except Booking.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Booking not found"}, status=404)


# 🟢 AJAX RESCHEDULE
@require_POST
def ajax_reschedule(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
        nd = request.POST.get("new_date")
        ns = request.POST.get("new_start_time")
        ne = request.POST.get("new_end_time")
        if not (nd and ns and ne):
            return JsonResponse({"ok": False, "error": "Missing data"})
        new_date = datetime.strptime(nd, "%Y-%m-%d").date()
        new_start = datetime.strptime(ns, "%H:%M").time()
        new_end = datetime.strptime(ne, "%H:%M").time()
        b.reschedule(new_date, new_start, new_end)
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


# 🟢 AJAX ACCEPT RESCHEDULE (COACH)
@require_POST
def ajax_accept_reschedule(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
        if b.status == "rescheduled":
            b.status = "confirmed"
            b.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "error": "Not rescheduled"})
    except Booking.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Booking not found"}, status=404)


# 🟢 AJAX REJECT RESCHEDULE (COACH)
@require_POST
def ajax_reject_reschedule(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
        if b.status == "rescheduled":
            b.status = "cancelled"
            b.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "error": "Not rescheduled"})
    except Booking.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Booking not found"}, status=404)


# 🟢 AJAX CONFIRM BOOKING (COACH)
@require_POST
def ajax_confirm_booking(request, booking_id):
    try:
        b = Booking.objects.get(id=booking_id)
        if b.status == "pending":
            b.status = "confirmed"
            b.save()
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "error": "Already confirmed"})
    except Booking.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Booking not found"}, status=404)

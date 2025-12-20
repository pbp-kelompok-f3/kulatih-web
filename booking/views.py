from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import models
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import requests


from .models import Booking
from users.models import Coach, Member


# Auto complete booking yang udah lewat
def auto_complete_bookings():
    """
    Update otomatis semua booking yang sudah lewat jadi 'completed',
    berlaku untuk member & coach, tanpa perlu cron job.
    """
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    # Booking yang statusnya masih aktif
    active_bookings = Booking.objects.filter(
        status__in=["pending", "confirmed", "rescheduled"]
    )

    # Booking yang tanggalnya sudah lewat atau waktu berakhirnya sudah lewat
    expired_bookings = active_bookings.filter(
        models.Q(date__lt=today) |
        models.Q(date=today, end_time__lt=current_time)
    )

    count = 0
    for booking in expired_bookings:
        booking.status = "completed"
        booking.save(update_fields=["status"])
        count += 1

    if count > 0:
        print(f"[AutoComplete] {count} booking(s) marked as completed.")


# 🟢 LIST BOOKINGS
@login_required(login_url='/accounts/login/')
def booking_list(request):
    # Auto update setiap kali halaman dibuka
    auto_complete_bookings()

    today = timezone.localdate()
    is_coach = hasattr(request.user, "coach")
    is_member = hasattr(request.user, "member")

    bookings = Booking.objects.none()
    if is_coach:
        bookings = Booking.objects.filter(coach=request.user.coach).order_by('-date', '-start_time')
    elif is_member:
        bookings = Booking.objects.filter(member=request.user.member).order_by('-date', '-start_time')

    context = {
        "bookings": bookings,
        "today": today,
        "is_coach": is_coach,
        "is_member": is_member,
    }
    return render(request, "booking/booking_list.html", context)

# 🟢 CREATE BOOKING
@login_required(login_url='/accounts/login/')
def create_booking(request, coach_id):
    # 🚫 Jika user adalah coach, langsung tolak
    if hasattr(request.user, "coach"):
        messages.error(request, "Coaches cannot create bookings.")
        return redirect("booking:list")

    # 🚫 Jika user bukan member juga, tolak
    if not hasattr(request.user, "member"):
        messages.error(request, "Only members can create bookings.")
        return redirect("users:coach_list")

    # ✅ Kalau lolos dua kondisi di atas, berarti dia member → boleh booking
    coach = get_object_or_404(Coach, id=coach_id)
    member = request.user.member

    if request.method == "POST":
        location = request.POST.get("location")
        datetime_str = request.POST.get("date")

        if not (location and datetime_str):
            messages.error(request, "Please fill all fields.")
            return render(request, "booking/create_booking.html", {'coach': coach})

        try:
            dt = timezone.make_aware(datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M"))
            date = dt.date()
            start_time = dt.time()
            end_time = (dt + timedelta(hours=1)).time()
        except ValueError:
            messages.error(request, "Invalid date/time format.")
            return render(request, "booking/create_booking.html", {'coach': coach})

        if dt < timezone.now():
            messages.error(request, "Booking date and time cannot be in the past.")
            return render(request, "booking/create_booking.html", {'coach': coach})

        # Cek konflik waktu
        if Booking.is_conflict(coach, date, start_time, end_time):
            messages.error(request, f"Coach {coach.user.get_full_name()} is unavailable at the selected time.")
            return render(request, "booking/create_booking.html", {'coach': coach})

        # Simpan booking
        Booking.objects.create(
            member=member,
            coach=coach,
            date=date,
            start_time=start_time,
            end_time=end_time,
            location=location,
            status="pending",
        )

        messages.success(request, f"Booking created successfully with coach {coach.user.get_full_name()}!")
        return redirect("booking:list")

    context = {'coach': coach}
    return render(request, "booking/create_booking.html", context)



# 🟢 EDIT BOOKING
@login_required(login_url='/accounts/login/')
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Ensure only the member who made the booking can edit
    if request.user.member != booking.member:
        messages.error(request, "You are not authorized to edit this booking.")
        return redirect('booking:list')

    if request.method == 'POST':
        location = request.POST.get("location")
        datetime_str = request.POST.get("date")
        status = request.POST.get('status', booking.status)

        if not (location and datetime_str):
            messages.error(request, "Please fill all fields.")
            return render(request, "booking/edit_booking.html", {'booking': booking})

        try:
            dt = timezone.make_aware(datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M"))
            date = dt.date()
            start_time = dt.time()
            end_time = (dt + timedelta(hours=1)).time()
        except (TypeError, ValueError):
            messages.error(request, "Invalid date/time format.")
            return render(request, 'booking/edit_booking.html', {'booking': booking})

        if start_time >= end_time:
            messages.error(request, "Start time must be before end time.")
            return render(request, 'booking/edit_booking.html', {'booking': booking})

        # Check for conflicts with the same coach
        if Booking.is_conflict(booking.coach, date, start_time, end_time, exclude_booking_id=booking.id):
            messages.error(request, f"Schedule conflicts with coach {booking.coach.user.get_full_name()}.")
            return render(request, 'booking/edit_booking.html', {'booking': booking})

        # Update booking fields
        booking.location = location
        booking.date = date
        booking.start_time = start_time
        booking.end_time = end_time
        booking.status = status
        booking.save()

        messages.success(request, "Booking updated successfully!")
        return redirect('booking:list')

    context = {
        'booking': booking,
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


# 🟢 AJAX RESCHEDULE (MEMBER)
@require_POST
def ajax_reschedule(request, booking_id):
    try:
        import json
        b = Booking.objects.get(id=booking_id)
        data = json.loads(request.body.decode("utf-8"))
        new_date_str = data.get("date")
        if not new_date_str:
            return JsonResponse({"ok": False, "error": "Missing date"})

        from datetime import datetime, timedelta
        new_dt = datetime.strptime(new_date_str, "%Y-%m-%dT%H:%M")
        new_date = new_dt.date()
        new_start = new_dt.time()
        new_end = (new_dt + timedelta(hours=1)).time()

        b.reschedule(new_date, new_start, new_end)

        # Kirim notifikasi ke coach (disimpan via Django messages)
        messages.info(request, f"Reschedule request sent to {b.coach.user.get_full_name()}!")

        return JsonResponse({"ok": True})

    except Booking.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Booking not found"}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)



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


@login_required
def booking_list_json(request):
    auto_complete_bookings()  # update otomatis

    user = request.user
    now = timezone.localtime()

    if hasattr(user, "coach"):
        bookings = Booking.objects.filter(coach=user.coach)
        role = "coach"
        user_id = user.coach.id
    elif hasattr(user, "member"):
        bookings = Booking.objects.filter(member=user.member)
        role = "member"
        user_id = user.member.id
    else:
        return JsonResponse({"ok": False, "error": "Invalid user role"}, status=400)

    bookings = bookings.order_by("-date", "-start_time")

    data = []
    for b in bookings:
        data.append({
            "id": b.id,
            "date": b.date.isoformat(),
            "start_time": b.start_time.strftime("%H:%M"),
            "end_time": b.end_time.strftime("%H:%M"),
            "location": b.location,
            "status": b.status,

            # Coach info
            "coach_name": b.coach.user.get_full_name(),
            "coach_id": str(b.coach.id),

            # Member info
            "member_name": b.member.user.get_full_name(),
            "member_id": str(b.member.id),

            "is_past": b.date < now.date() or (b.date == now.date() and b.end_time < now.time()),
        })

    return JsonResponse({
        "ok": True,
        "role": role,
        "user_id": str(user_id),
        "count": len(data),
        "items": data
    })


@login_required
def create_booking_json(request, coach_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    if hasattr(request.user, "coach"):
        return JsonResponse({"ok": False, "error": "Coach cannot create booking"}, status=403)

    if not hasattr(request.user, "member"):
        return JsonResponse({"ok": False, "error": "Only members can book"}, status=403)

    body = json.loads(request.body)
    location = body.get("location")
    datetime_str = body.get("datetime")

    if not (location and datetime_str):
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    coach = get_object_or_404(Coach, id=coach_id)
    member = request.user.member

    try:
        dt = timezone.make_aware(datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M"))
        date = dt.date()
        start_time = dt.time()
        end_time = (dt + timedelta(hours=1)).time()
    except:
        return JsonResponse({"ok": False, "error": "Invalid datetime format"}, status=400)

    if dt < timezone.now():
        return JsonResponse({"ok": False, "error": "Cannot book in the past"}, status=400)

    if Booking.is_conflict(coach, date, start_time, end_time):
        return JsonResponse({"ok": False, "error": "Coach unavailable at that time"}, status=409)

    b = Booking.objects.create(
        member=member,
        coach=coach,
        date=date,
        start_time=start_time,
        end_time=end_time,
        location=location,
        status="pending",
    )

    return JsonResponse({"ok": True, "id": b.id})

@login_required
def edit_booking_json(request, booking_id):
    if request.method != "PUT":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    body = json.loads(request.body)
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user.member != booking.member:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    location = body.get("location")
    datetime_str = body.get("datetime")
    status = body.get("status", booking.status)

    if not (location and datetime_str):
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    try:
        dt = timezone.make_aware(datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M"))
        date = dt.date()
        start_time = dt.time()
        end_time = (dt + timedelta(hours=1)).time()
    except:
        return JsonResponse({"ok": False, "error": "Invalid datetime format"}, status=400)

    if Booking.is_conflict(booking.coach, date, start_time, end_time, exclude_booking_id=booking_id):
        return JsonResponse({"ok": False, "error": "Schedule conflict"}, status=409)

    booking.location = location
    booking.date = date
    booking.start_time = start_time
    booking.end_time = end_time
    booking.status = status
    booking.save()

    return JsonResponse({"ok": True})

@login_required
def cancel_booking_json(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)
    b.status = "cancelled"
    b.save()

    return JsonResponse({"ok": True})

@login_required
def reschedule_json(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    body = json.loads(request.body)
    dt_str = body.get("datetime")

    if not dt_str:
        return JsonResponse({"ok": False, "error": "Missing datetime"}, status=400)

    try:
        new_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
        new_dt = timezone.make_aware(new_dt)
    except:
        return JsonResponse({"ok": False, "error": "Invalid datetime"}, status=400)

    new_date = new_dt.date()
    new_start = new_dt.time()
    new_end = (new_dt + timedelta(hours=1)).time()

    try:
        b.reschedule(new_date, new_start, new_end)
        return JsonResponse({"ok": True})
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

@login_required
def accept_reschedule_json(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    if b.status != "rescheduled":
        return JsonResponse({"ok": False, "error": "Not rescheduled"}, status=400)

    b.status = "confirmed"
    b.save()

    return JsonResponse({"ok": True})

@login_required
def reject_reschedule_json(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    if b.status != "rescheduled":
        return JsonResponse({"ok": False, "error": "Not rescheduled"}, status=400)

    b.status = "cancelled"
    b.save()

    return JsonResponse({"ok": True})


@login_required
def confirm_booking_json(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    if b.status != "pending":
        return JsonResponse({"ok": False, "error": "Already confirmed"}, status=400)

    b.status = "confirmed"
    b.save()

    return JsonResponse({"ok": True})

@csrf_exempt
def api_list_bookings(request):
    # sementara tanpa auth, biar Flutter jalan dulu
    bookings = Booking.objects.all().order_by("-date", "-start_time")

    data = []
    for b in bookings:
        data.append({
            "id": b.id,
            "coach_id": str(b.coach.id),
            "coach_name": b.coach.user.get_full_name(),
            "member_name": b.member.user.get_full_name(),
            "sport": b.coach.sport if hasattr(b.coach, "sport") else "",
            "location": b.location,
            "date": b.date.isoformat(),
            "start_time": b.start_time.strftime("%H:%M"),
            "end_time": b.end_time.strftime("%H:%M"),
            "status": b.status,
        })

    return JsonResponse({"bookings": data}, status=200)

@csrf_exempt
def api_create_booking(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    coach_id = data.get("coach_id")
    location = data.get("location")
    dt_str = data.get("date")

    if not (coach_id and location and dt_str):
        return JsonResponse({"error": "Missing fields"}, status=400)

    coach = Coach.objects.get(id=coach_id)

    dt = timezone.make_aware(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S"))
    date = dt.date()
    start_time = dt.time()
    end_time = (dt + timedelta(hours=1)).time()

    booking = Booking.objects.create(
        coach=coach,
        member=request.user.member,   # kalau kamu mau pakai auth
        date=date,
        start_time=start_time,
        end_time=end_time,
        location=location,
        status="pending"
    )

    return JsonResponse({"ok": True, "id": booking.id})

@csrf_exempt
def api_reschedule_booking(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    new_start = data.get("new_start_time")
    new_end = data.get("new_end_time")

    if not new_start or not new_end:
        return JsonResponse({"error": "Missing time fields"}, status=400)

    b = Booking.objects.get(id=booking_id)

    new_start_dt = datetime.fromisoformat(new_start)
    new_end_dt = datetime.fromisoformat(new_end)

    b.start_time = new_start_dt.time()
    b.end_time = new_end_dt.time()
    b.date = new_start_dt.date()
    b.status = "rescheduled"
    b.save()

    return JsonResponse({"ok": True})

@csrf_exempt
def api_cancel_booking(request, booking_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    b = Booking.objects.get(id=booking_id)
    b.status = "cancelled"
    b.save()

    return JsonResponse({"ok": True})

@csrf_exempt
def api_confirm_booking(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        booking.status = "confirmed"
        booking.save()
        return JsonResponse({"status": "success"})

@csrf_exempt
def api_accept_reschedule(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        booking.status = "confirmed"
        booking.save()
        return JsonResponse({"status": "success"})

@csrf_exempt
def api_reject_reschedule(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        booking.status = "cancelled"
        booking.save()
        return JsonResponse({"status": "success"})

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)

import os, json
from django.core.mail import EmailMultiAlternatives
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from qstash import Receiver
from .models import Book

# @shared_task
# def send_schedule_change_notifications(schedule_id, old_data, new_data):
@csrf_exempt
def send_schedule_change_notifications(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    message_id = request.headers["Upstash-Message-Id"]
    key = f"processed:{message_id}"

    if cache.get(key):
        return JsonResponse({"status": "already processed"})

    signature = request.headers.get("Upstash-Signature")
    if not signature:
        return HttpResponseForbidden("Missing QStash Signature")

    receiver = Receiver(
        current_signing_key=os.environ.get("QSTASH_CURRENT_SIGNING_KEY"),
        next_signing_key=os.environ.get("QSTASH_NEXT_SIGNING_KEY"),
    )

    try:
        body_str = request.body.decode("utf-8")
        receiver.verify(body=body_str, signature=signature)
    except Exception:
        return HttpResponseForbidden("Invalid QStash Signature")

    try:
        data = json.loads(body_str)
        schedule_id = data.get("schedule_id")
        old_data = data.get("old_data")
        new_data = data.get("new_data")
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    bookings = (
        Book.objects.filter(schedule_id=schedule_id, status="BOOKED")
        .select_related("user")
    )

    for booking in bookings:
        email = getattr(booking.user, "email", None)
        if not email:
            continue

        context = {
            "passenger_name": getattr(booking.user, "first_name", None) or "Passenger",
            "old_data": old_data,
            "new_data": new_data,
        }

        html_content = render_to_string("schedule_changed.html", context)

        message = EmailMultiAlternatives(
            subject="Important: Your Bus Schedule Has Been Updated",
            body="Your bus schedule has been updated. Please check the updated schedule details.",
            to=[email],
        )
        message.attach_alternative(html_content, "text/html")
        message.send()

    cache.set(key, "1", timeout=2700)

    return JsonResponse({"status": "success", "processed": len(bookings)})


@require_POST
def cleanup_seat_inventory(request):
    auth_header = request.headers.get("Authorization")

    expected = f"Bearer {os.environ.get('CRON_SECRET_KEY')}"

    if auth_header != expected:
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    completed_schedules = Schedule.objects.filter(
        departure_time__lt=timezone.now()
    )

    deleted_count, _ = SeatInventory.objects.filter(
        schedule__in=completed_schedules
    ).delete()

    return JsonResponse({"message": f"Cleanup completed. Deleted {deleted_count} rows"})
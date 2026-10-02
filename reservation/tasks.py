import os, json
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from qstash import Receiver
from .models import Book


@csrf_exempt
def send_schedule_change_notifications(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

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

    return JsonResponse({"status": "success", "processed": len(bookings)})
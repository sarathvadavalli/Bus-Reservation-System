import os
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Book
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from qstash import Receiver


# @shared_task
# def send_schedule_change_notifications(schedule_id, old_data, new_data):
@csrf_exempt
def send_schedule_change_notifications(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    signature = request.headers.get("Upstash-Signature")
    receiver = Receiver(
        current_signing_key=os.environ.get("QSTASH_CURRENT_SIGNING_KEY"),
        next_signing_key=os.environ.get("QSTASH_NEXT_SIGNING_KEY"),
    )

    try:
        receiver.verify(body=request.body.decode("utf-8"), signature=signature)
    except Exception:
        return HttpResponseForbidden("Invalid QStash Signature")

    try:
        data = json.loads(request.body)
        schedule_id = data.get("schedule_id")
        old_data = data.get("old_data")
        new_data = data.get("new_data")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    bookings = (
        Book.objects
        .filter(schedule_id=schedule_id, status='BOOKED')
        .select_related("user")
    )

    for booking in bookings:
        email = booking.user.email
        print(email)

        if not email:
            continue

        context = {
            "passenger_name": booking.user.first_name or "Passenger",
            "old_data": old_data,
            "new_data": new_data,
        }

        html_content = render_to_string(
            "schedule_changed.html",
            context
        )

        message = EmailMultiAlternatives(
            subject="Important: Your Bus Schedule Has Been Updated",
            body=(
                "Your bus schedule has been updated. "
                "Please check the updated schedule details."
            ),
            to=[email],
        )

        message.attach_alternative(html_content, "text/html")
        message.send()
        print("Email sent to:", email)
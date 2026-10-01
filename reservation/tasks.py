from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Book


@shared_task
def send_schedule_change_notifications(schedule_id, old_data, new_data):
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
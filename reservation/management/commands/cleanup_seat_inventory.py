from django.core.management.base import BaseCommand
from django.utils import timezone
from reservation.models import SeatInventory, Schedule1


class Command(BaseCommand):
    help = "Delete SeatInventory for completed schedules"

    def handle(self, *args, **kwargs):
        completed_schedules = Schedule1.objects.filter(
            departure_time__lt=timezone.now()
        )

        deleted_count, _ = SeatInventory.objects.filter(
            schedule__in=completed_schedules
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} SeatInventory rows."
            )
        )
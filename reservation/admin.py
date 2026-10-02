import os
from django.contrib import admin
from .models import Schedule, Buses, Profile, SeatInventory
from django.db import transaction
from django.core.cache import cache
from .tasks import send_schedule_change_notifications
from qstash import QStash

client = QStash(os.environ.get("QSTASH_TOKEN"))

def seat_creation(capacity):
    seats = []
    for i in range(1, capacity + 1):
        qu = i // 4
        rem = i % 4
        if rem == 0:
            row = chr(ord('A') + qu - 1)
            num = '4'
        else:
            row = chr(ord('A') + qu)
            num = str(rem)

        seats.append(row + num)

    return seats


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    readonly_fields = ("rem",)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)

            seats = seat_creation(obj.bus.capacity)
            seat_objects = [
                SeatInventory(schedule=obj, seat_no=seat, status="AVAILABLE")
                for seat in seats
            ]

            SeatInventory.objects.bulk_create(seat_objects)

        else:
            old_obj = Schedule.objects.get(pk=obj.pk)

            changed = (
                old_obj.source != obj.source or
                old_obj.dest != obj.dest or
                old_obj.arrival_datetime != obj.arrival_datetime or
                old_obj.departure_datetime != obj.departure_datetime
            )

            if changed:
                super().save_model(request, obj, form, change)

                arrival_date_old = old_obj.arrival_datetime.date()
                arrival_date_new = obj.arrival_datetime.date()
                key1 = f"bus_search_{old_obj.source}_{old_obj.dest}_{str(arrival_date_old)}"
                key2 = f"bus_search_{obj.source}_{obj.dest}_{str(arrival_date_new)}"
                cache.delete(key1)
                cache.delete(key2)

                old_data = {
                    "source": old_obj.source,
                    "dest": old_obj.dest,
                    "arrival_datetime": str(old_obj.arrival_datetime)[:16],
                    "departure_datetime": str(old_obj.departure_datetime)[:16],
                }

                new_data = {
                    "source": obj.source,
                    "dest": obj.dest,
                    "arrival_datetime": str(obj.arrival_datetime)[:16],
                    "departure_datetime": str(obj.departure_datetime)[:16],
                }

                # send_schedule_change_notifications.delay(
                #     obj.schedule_id,
                #     old_data,
                #     new_data
                # )
                client.message.publish_json(
                    url="https://bus-reservation-system-b4rd.vercel.app/api/webhooks/schedule-changed/",
                    body={
                        "schedule_id": obj.schedule_id,
                        "old_data": old_data,
                        "new_data": new_data
                    }
                )


admin.site.register(Buses)
admin.site.register(Profile)
from django.contrib import admin
from .models import Schedule1, Buses, Profile, SeatInventory
from django.db import transaction


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


@admin.register(Schedule1)
class ScheduleAdmin(admin.ModelAdmin):
    readonly_fields = ("rem",)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None

        super().save_model(request, obj, form, change)

        if is_new:
            seats = seat_creation(obj.bus.capacity)
            seat_objects = [
                SeatInventory(schedule=obj, seat_no=seat, status="AVAILABLE")
                for seat in seats
            ]

            SeatInventory.objects.bulk_create(seat_objects)


admin.site.register(Buses)
admin.site.register(Profile)
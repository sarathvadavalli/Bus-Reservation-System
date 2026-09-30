from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phno = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.user.username


class Buses(models.Model):
    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=30)
    capacity = models.IntegerField(default=30)
    price = models.DecimalField(decimal_places=2, max_digits=6, default=0.0)
    
    class Meta:
        verbose_name_plural = "List of Busses"

    def __str__(self):
        return self.bus_name
    

class Schedule1(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    bus = models.ForeignKey(Buses, on_delete=models.CASCADE, null=True, blank=True)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    rem = models.IntegerField()
    date = models.DateField()
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    status = models.CharField(max_length=20, default='AVAILABLE')

    def save(self, *args, **kwargs):
        if self.rem is None:        
            self.rem = self.bus.capacity
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "List of Schedules"
        constraints = [ models.UniqueConstraint(
                            fields=['bus', 'date', 'departure_time'], name='unique_schedule_combination'
                        )
                    ]

    def __str__(self):
        return self.bus.bus_name + " - " + self.source + " to " + self.dest + " on " + str(self.date)


class SeatInventory(models.Model):
    schedule = models.ForeignKey(
        Schedule1,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    seat_no = models.CharField(max_length=10)
    status = models.CharField(
        max_length=20,
        choices=[
            ("AVAILABLE", "Available"),
            ("BOOKED", "Booked"),
        ],
        default="AVAILABLE",
    )

    class Meta:
        verbose_name_plural = "List of Seats"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "seat_no"],
                name="unique_seat_schedule",
            )
        ]
    
    def __str__(self):
        return str(self.schedule_id) + " - " + str(self.seat_no) 

    
class Book(models.Model):
    bookid = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    schedule = models.ForeignKey(Schedule1, on_delete=models.CASCADE, null=True, blank=True)
    nos = models.DecimalField(decimal_places=0, max_digits=2)
    seats = models.CharField(max_length=50, default="")
    price = models.DecimalField(decimal_places=2, max_digits=6)
    time = models.DateTimeField()
    status = models.CharField(
        choices=[
            ('B', 'Booked'),
            ('C', 'Cancelled')
        ], 
        default='U', max_length=20
    )

    class Meta:
        verbose_name_plural = "List of Books"


    def __str__(self):
        return str(self.bookid) + " - " + str(self.user) + " - " + str(self.schedule)
    

# class Seat(models.Model):
#     seat_id = models.AutoField(primary_key=True)
#     schedule_id = models.ForeignKey(Schedule1, on_delete=models.CASCADE)
#     book_id = models.ForeignKey(Book, on_delete=models.CASCADE)
#     seat_no = models.CharField(max_length=5)

#     class Meta:
#         verbose_name_plural = "List of Seats"
#         constraints = [ models.UniqueConstraint(
#                             fields=['schedule_id', 'seat_no'], name='unique_seat_combination'
#                         )
#                     ]

#     def __str__(self):
#         return str(self.schedule_id) + " - " + str(self.seat_no)
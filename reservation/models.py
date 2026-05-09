from django.db import models
from django.contrib.auth.models import User

# Create your models here.
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
    bus_id = models.ForeignKey(Buses, on_delete=models.CASCADE)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    rem = models.IntegerField()
    date = models.DateField()
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    status = models.CharField(max_length=20, default='AVAILABLE')

    def save(self, *args, **kwargs):
        if not self.rem:        
            self.rem = self.bus_id.capacity
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "List of Schedules"
        constraints = [ models.UniqueConstraint(
                            fields=['bus_id', 'date', 'departure_time'], name='unique_schedule_combination'
                        )
                    ]

    def __str__(self):
        return self.bus_id.bus_name + " - " + self.source + " to " + self.dest + " on " + str(self.date)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phno = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.user.username
    
class Book(models.Model):
    BOOKED = 'B'
    CANCELLED = 'C'

    TICKET_STATUSES = ((BOOKED, 'Booked'),
                       (CANCELLED, 'Cancelled'),)
    
    bookid = models.AutoField(primary_key=True)
    userid =models.IntegerField(default=0)
    schedule_id = models.IntegerField(default=0)
    nos = models.DecimalField(decimal_places=0, max_digits=2)
    price = models.DecimalField(decimal_places=2, max_digits=6)
    time = models.DateTimeField()
    status = models.CharField(choices=TICKET_STATUSES, default=BOOKED, max_length=20)

    class Meta:
        verbose_name_plural = "List of Books"

    def __str__(self):
        return str(self.bookid) + " - " + str(self.userid) + " - " + str(self.schedule_id)
    
class Seat(models.Model):
    seat_id = models.AutoField(primary_key=True)
    schedule_id = models.ForeignKey(Schedule1, on_delete=models.CASCADE)
    book_id = models.ForeignKey(Book, on_delete=models.CASCADE)
    seat_no = models.CharField(max_length=5)
    # status = models.CharField(max_length=20, default='AVAILABLE')

    class Meta:
        verbose_name_plural = "List of Seats"
        constraints = [ models.UniqueConstraint(
                            fields=['schedule_id', 'seat_no'], name='unique_seat_combination'
                        )
                    ]

    def __str__(self):
        return str(self.schedule_id) + " - " + str(self.seat_no)
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=30)
    capacity = models.IntegerField(default=30)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    rem = models.IntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=6, default=0.0)
    date = models.DateField()
    time = models.TimeField()

    def save(self, *args, **kwargs):
        if not self.rem:
            # Initialize attribute3 with the value of attribute1
            self.rem = self.capacity
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "List of Busses"
        constraints = [ models.UniqueConstraint(
                            fields=['bus_name', 'date', 'time'], name='unique_bus_combination'
                        )
                    ]

    def __str__(self):
        return self.bus_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phno = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.user.username
    
class Book(models.Model):
    BOOKED = 'B'
    CANCELLED = 'C'

    TICKET_STATUSES = ((BOOKED, 'Booked'),
                       (CANCELLED, 'Cancelled'),)
    
    userid =models.DecimalField(decimal_places=0, max_digits=2)
    bus_name = models.CharField(max_length=30)
    src = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    nos = models.DecimalField(decimal_places=0, max_digits=2)
    price = models.DecimalField(decimal_places=2, max_digits=6)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(choices=TICKET_STATUSES, default=BOOKED, max_length=2)

    class Meta:
        verbose_name_plural = "List of Books"

    def __str__(self):
        return self.email
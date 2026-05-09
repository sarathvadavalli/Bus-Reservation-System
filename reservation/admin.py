from django.contrib import admin
from .models import Schedule1, Buses, Profile

# Register your models here.
class BusAdmin(admin.ModelAdmin):
        exclude = ('rem',)

admin.site.register(Schedule1, BusAdmin)
admin.site.register(Buses)
admin.site.register(Profile)
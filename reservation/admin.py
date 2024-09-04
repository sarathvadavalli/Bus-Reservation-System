from django.contrib import admin
from .models import Bus, UserProfile

# Register your models here.
class BusAdmin(admin.ModelAdmin):
        exclude = ('rem',)

admin.site.register(Bus, BusAdmin)
admin.site.register(UserProfile)
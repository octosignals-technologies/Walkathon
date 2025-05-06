from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Participant, CheckIn

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'name', 'email', 'phone_number', 'walking_distance_km', 'registered_at')

@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('participant', 'checkin_time')

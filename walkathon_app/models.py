from django.db import models
from django.utils import timezone

class Participant(models.Model):
    unique_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    walking_distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    registered_at = models.DateTimeField(auto_now_add=True)

    # New fields based on updated registration
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')], null=True, blank=True)
    working_professional = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    o9_employee = models.CharField(max_length=3, choices=[('Yes', 'Yes'), ('No', 'No')], null=True, blank=True)
    employee_code = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.unique_id})"

class CheckIn(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    checkin_time = models.DateTimeField(default=timezone.now)

    def _str_(self):
        return f"Check-in: {self.participant.name} at {self.checkin_time}"
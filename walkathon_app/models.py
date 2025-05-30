import uuid
from django.db import models
from django.utils import timezone

def generate_unique_id():
    return str(uuid.uuid4())[:8].upper()  # Short unique ID

class Participant(models.Model):
    unique_id = models.CharField(max_length=20, unique=True, default=generate_unique_id, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    walking_distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    registered_at = models.DateTimeField(auto_now_add=True)

    # Optional additional fields
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')],
        null=True, blank=True
    )
    working_professional = models.CharField(
        max_length=3,
        choices=[('Yes', 'Yes'), ('No', 'No')],
        null=True, blank=True
    )
    o9_employee = models.CharField(
        max_length=3,
        choices=[('Yes', 'Yes'), ('No', 'No')],
        null=True, blank=True
    )
    employee_code = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.unique_id})"

class CheckIn(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    checkin_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Check-in: {self.participant.name} at {self.checkin_time}"

class CommunicationLog(models.Model):
        TYPE_CHOICES = [
            ('email', 'Email'),
            ('whatsapp', 'WhatsApp'),
        ]
        STATUS_CHOICES = [
            ('email sent', 'Email Sent'),
            ('whatsapp sent', 'WhatsApp Sent'),
        ]

        participant = models.ForeignKey('Participant', on_delete=models.CASCADE)
        type = models.CharField(max_length=255, choices=TYPE_CHOICES)
        value = models.CharField(max_length=255)
        status = models.CharField(max_length=255, choices=STATUS_CHOICES)
        created_on = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.type} log for {self.participant.name}"
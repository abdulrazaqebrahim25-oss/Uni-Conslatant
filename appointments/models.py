from django.db import models
from accounts.models import StudentProfile, AdvisorProfile

# Create your models here.
class Appointment(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("done", "Done"),
        ("canceled", "Canceled"),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    advisor = models.ForeignKey(
        AdvisorProfile,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    def __str__(self):
        return f"{self.student.user.username} with {self.advisor.user.username}"
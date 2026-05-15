from django.db import models
from django.contrib.auth.models import AbstractUser

from main_app.models import Major, Course


class User(AbstractUser):

    ROLE_CHOICES = [
        ("student", "Student"),
        ("advisor", "Advisor"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="student"
    )

    def __str__(self):

        full_name = self.get_full_name()

        if full_name:
            return full_name

        return self.username


class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students"
    )

    university_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )

    completed_courses = models.ManyToManyField(
        Course,
        related_name="completed_by_students",
        blank=True
    )

    def __str__(self):
        return str(self.user)


class AdvisorProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="advisor_profile"
    )

    office = models.CharField(
        max_length=100,
        blank=True
    )

    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advisors"
    )

    def __str__(self):
        return str(self.user)
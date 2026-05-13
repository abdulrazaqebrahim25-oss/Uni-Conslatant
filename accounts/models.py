from django.db import models
from django.contrib.auth.models import AbstractUser
from main_app.models import Major, Course
# Create your models here.



class User(AbstractUser):

    ROLE_CHOICES = [
        ("student", "Student"),
        ("advisor", "Advisor"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    def __str__(self):
        return self.username





class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    university_id = models.CharField(
        max_length=20,
        blank=True
    )

    completed_courses = models.ManyToManyField(
    Course,
    related_name="completed_by_students",
    blank=True
    )

    def __str__(self):
        return self.user.username


class AdvisorProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    office = models.CharField(
        max_length=100,
        blank=True
    )

    major = models.ForeignKey(
    Major,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
    )

    def __str__(self):
        return self.user.username
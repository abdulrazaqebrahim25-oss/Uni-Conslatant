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

    BUDGET_CHOICES = [
    ("low", "Low Budget (150-350 BD)"),
    ("medium", "Medium Budget (351-700 BD)"),
    ("high", "Excellent Budget (701+ BD)"),
    ]

    SEMESTER_PREFERENCE_CHOICES = [
        (2, "2 Semesters"),
        (3, "3 Semesters"),
    ]

    ENTRY_SEMESTER_CHOICES = [
        ("fall", "Fall"),
        ("spring", "Spring"),
        ("summer", "Summer"),
    ]

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

    entry_year = models.PositiveIntegerField()

    entry_semester = models.CharField(
        max_length=20,
        choices=ENTRY_SEMESTER_CHOICES
    )

    preferred_semesters_per_year = models.IntegerField(
        choices=SEMESTER_PREFERENCE_CHOICES,
        default=3
    )

    budget_level = models.CharField(
        max_length=20,
        choices=BUDGET_CHOICES,
        default="medium"
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
    
class AcademicSemester(models.Model):

    SEMESTER_CHOICES = [
        ("fall", "Fall"),
        ("spring", "Spring"),
        ("summer", "Summer"),
    ]

    SEMESTER_HOURS = {
        "fall": (12, 20),
        "spring": (12, 20),
        "summer": (3, 9),
    }

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="academic_semesters"
    )

    semester_type = models.CharField(
        max_length=20,
        choices=SEMESTER_CHOICES
    )

    academic_year = models.CharField(
        max_length=20
    )

    start_date = models.DateField()

    end_date = models.DateField()

    completed_courses = models.ManyToManyField(
        Course,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.student} - {self.semester_type} {self.academic_year}"

    @property
    def min_hours(self):

        return self.SEMESTER_HOURS[self.semester_type][0]

    @property
    def max_hours(self):

        return self.SEMESTER_HOURS[self.semester_type][1]
from django.db import models

# Create your models here.

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    credit = models.IntegerField()

    def __str__(self):
        return f"{self.code} - {self.name}"


class Major(models.Model):
    name = models.CharField(max_length=250)

    # ManyToMany with extra field through MajorCourse
    courses = models.ManyToManyField(
        Course,
        through="MajorCourse",
        related_name="majors"
    )

    def __str__(self):
        return self.name


class MajorCourse(models.Model):
    TYPE_CHOICES = [
        ("Mandatory", "Mandatory"),
        ("Elective", "Elective"),
    ]

    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        unique_together = ("major", "course")  # Prevent duplicates

    def __str__(self):
        return f"{self.course.name} in {self.major.name} ({self.type})"
    

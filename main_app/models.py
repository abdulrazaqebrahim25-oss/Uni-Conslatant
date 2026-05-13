from django.db import models

# Create your models here.

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    credit = models.IntegerField()

    #A course can require other courses before it
    #'self' means it links to the same course table
    #symmetrical=False means "A requires B", doesn't mean "B requires A"
    prerequisotes = models.ManyToManyField(
        'self',
        symmetrical = False,
        blank=True,
        related_name='required_for'
    )

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
    
class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255) #made longer for hashed passwords
    major = models.ForeignKey(Major, on_delete=models.PROTECT)

    def __str__(self):
        return self.name
    

class Advisor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Appointment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("done", "Done"),
        ("canceled", "Canceled"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    advisor = models.ForeignKey(Advisor, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default = "pending")

    def __str__(self):
        return f"{self.student.name} with {self.advisor.name}"
    

#Track which courses a student has completed
class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='completed_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='students_completed')
    date_completed = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course') #logic: a student cannot complete the same course twice

    def __str__(self):
        return f"{self.student.name} - {self.course.name}"
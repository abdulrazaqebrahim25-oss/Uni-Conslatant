from django.db import models

# Create your models here.
class Major(models.Model):

    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name 
    
class Course(models.Model):
    LEVEL_CHOICES = [
        (1, "First Year"),
        (2, "Second Year"),
        (3, "Third Year"),
        (4, "Final Year"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    level = models.IntegerField(choices=LEVEL_CHOICES)

    majors = models.ManyToManyField(Major)

    def __str__(self):
        return self.name 
    
class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    major = models.ForeignKey(Major, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Advisor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

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
    advisor = models.ForeignKey(Advisor, on_delete=models.CASCADE)

    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.student.name} with {self.advisor.name}"
    
    
from django.contrib import admin

# Register your models here.

from .models import (
    Major,
    Course,
    Student,
    Advisor,
    Appointment
)

admin.site.register(Major)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(Advisor)
admin.site.register(Appointment)
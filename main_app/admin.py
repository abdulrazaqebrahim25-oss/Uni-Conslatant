from django.contrib import admin
from .models import Major, Course, Student, Advisor, Appointment, MajorCourse, StudentCourse

# Register your models here.

admin.site.register(Major)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(Advisor)
admin.site.register(Appointment)
admin.site.register(StudentCourse)
admin.site.register(MajorCourse)
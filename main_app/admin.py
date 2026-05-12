from django.contrib import admin

# Register your models here.

from .models import (
    Major,
    Course,
    MajorCourse,

)

admin.site.register(Major)
admin.site.register(Course)
admin.site.register(MajorCourse)

from django.urls import path
from .views import create_appointment
from . import views 

urlpatterns = [
    path('create/', create_appointment, name='create_appointment'),
        path(
        'student/',
        views.student_appointments,
        name='student_appointments'
    ),
]
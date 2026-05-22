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
    path(
        'advisor/',
        views.advisor_appointments,
        name='advisor_appointments'
    ),

    path(
        'update-status/<int:appointment_id>/<str:new_status>/',
        views.update_appointment_status,
        name='update_appointment_status'
    ),

    path(
    "advisor/calendar/events/",
    views.advisor_calendar_events,
    name="advisor_calendar_events"
    ),

    path(
    "advisor/calendar/",
    views.advisor_calendar_view,
    name="advisor_calendar"
    ),

    path(
    "edit/<int:appointment_id>/",
    views.edit_appointment,
    name="edit_appointment"
    ),

    path(
    "delete/<int:appointment_id>/",
    views.delete_appointment,
    name="delete_appointment"
    ),

]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse

from .forms import AppointmentForm
from .models import Appointment
from accounts.models import StudentProfile


@login_required
def create_appointment(request):

    student = request.user.student_profile

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save(commit=False)

            appointment.student = student

            if appointment.start_time < timezone.now():

                form.add_error(
                    "start_time",
                    "You cannot book an appointment in the past."
                )

                return render(request, "appointments/create.html", {
                    "form": form
                })

            overlapping = Appointment.objects.filter(
                advisor=appointment.advisor
            ).filter(
                start_time__lt=appointment.end_time,
                end_time__gt=appointment.start_time
            ).exclude(
                status="canceled"
            )

            if overlapping.exists():

                form.add_error(
                    None,
                    "This advisor already has another appointment during this time."
                )

                return render(request, "appointments/create.html", {
                    "form": form
                })

            appointment.save()

            return redirect("student_appointments")

    else:
        form = AppointmentForm()

    return render(request, "appointments/create.html", {
        "form": form
    })


@login_required
def student_appointments(request):

    student = request.user.student_profile

    appointments = Appointment.objects.filter(
        student=student
    ).order_by("-start_time")

    return render(request, "appointments/student_appointments.html", {
        "appointments": appointments
    })


@login_required
def advisor_appointments(request):

    advisor = request.user.advisor_profile

    appointments = Appointment.objects.filter(
        advisor=advisor
    ).order_by("-start_time")

    return render(request, "appointments/advisor_appointments.html", {
        "appointments": appointments
    })


@login_required
def update_appointment_status(request, appointment_id, new_status):

    if request.method != "POST":
        return redirect("advisor_appointments")

    advisor = request.user.advisor_profile

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        advisor=advisor
    )

    valid_statuses = ["approved", "done", "canceled"]

    if new_status in valid_statuses:
        appointment.status = new_status
        appointment.save()

    return redirect("advisor_appointments")


@login_required
def advisor_calendar_events(request):

    advisor = request.user.advisor_profile

    appointments = Appointment.objects.filter(
        advisor=advisor
    )

    events = []

    for appt in appointments:

        color = {
            "pending": "#f39c12",
            "approved": "#3498db",
            "done": "#2ecc71",
            "canceled": "#e74c3c",
        }.get(appt.status, "#95a5a6")

        events.append({
            "id": appt.id,
            "title": appt.student.user.get_full_name(),
            "start": appt.start_time.isoformat(),
            "end": appt.end_time.isoformat(),
            "color": color,
            "extendedProps": {
                "status": appt.status,
                "student": appt.student.user.username
            }
        })

    return JsonResponse(events, safe=False)


@login_required
def advisor_calendar_view(request):
    return render(request, "appointments/advisor_calendar.html")
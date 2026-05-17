from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from .forms import AppointmentForm
from .models import Appointment
from django.http import JsonResponse




@login_required
def create_appointment(request):

    student = request.user.student_profile

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save(commit=False)

            # ربط الطالب
            appointment.student = student

            # ❗ منع الحجز في الماضي
            if appointment.date < timezone.now():
                form.add_error("date", "You cannot book an appointment in the past.")
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

    appointments = Appointment.objects.filter(student=student)

    return render(
        request,
        'appointments/student_appointments.html',
        {
            'appointments': appointments
        }
    )

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Appointment


@login_required
def advisor_appointments(request):

    advisor = request.user.advisor_profile

    appointments = Appointment.objects.filter(advisor=advisor).order_by("-date")

    return render(
        request,
        "appointments/advisor_appointments.html",
        {
            "appointments": appointments
        }
    )

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

    appointments = Appointment.objects.filter(advisor=advisor)

    events = []

    for appt in appointments:
        events.append({
            "title": appt.student.user.get_full_name(),
            "start": appt.start_time.isoformat(),
            "end": appt.end_time.isoformat(),
            "status": appt.status,
        })

    return JsonResponse(events, safe=False)

@login_required
def advisor_calendar_view(request):
    return render(request, "appointments/advisor_calendar.html")
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import AppointmentForm
from .models import Appointment



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
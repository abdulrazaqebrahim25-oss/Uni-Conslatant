from django.shortcuts import render, redirect
from .forms import AppointmentForm
from .models import Appointment
from accounts.models import StudentProfile
from django.contrib.auth.decorators import login_required


def create_appointment(request):

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save(commit=False)

            student = StudentProfile.objects.get(
                user=request.user
            )

            appointment.student = student

            appointment.save()

            return redirect("home")

    else:
        form = AppointmentForm()

    return render(request, "appointments/create.html", {
        "form": form
    })


@login_required
def student_appointments(request):

    student = StudentProfile.objects.get(
        user=request.user
    )

    appointments = Appointment.objects.filter(
        student=student
    )

    return render(
        request,
        'appointments/student_appointments.html',
        {
            'appointments': appointments
        }
    )
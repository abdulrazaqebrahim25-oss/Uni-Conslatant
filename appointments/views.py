from django.shortcuts import render, redirect
from .forms import AppointmentForm
from .models import Appointment
from accounts.models import StudentProfile

# Create your views here.

def create_appointment(request):

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save(commit=False)

            appointment.student = request.user.studentprofile

            appointment.save()

            return redirect("home")

    else:
        form = AppointmentForm()

    return render(request, "appointments/create.html", {
        "form": form
    })
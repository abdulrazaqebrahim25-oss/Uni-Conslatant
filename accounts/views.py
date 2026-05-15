from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import StudentProfile, AdvisorProfile


# Create your views here.

def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            form.save()  

            return redirect("login")

    else:
        form = RegisterForm()

    return render(
        request,
        "registration/register.html",
        {"form": form}
    )




@login_required
def dashboard_view(request):

    student = request.user.student_profile

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "student": student
        }
    )

@login_required
def student_profile_view(request):

    student = request.user.student_profile

    return render(
        request,
        "dashboard/profile.html",
        {
            "student": student
        }
    )
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



# Advisor Dashboard View
@login_required
def advisor_dashboard_view(request):

    advisor = request.user.advisor_profile

    return render(
        request,
        "dashboard/advisor_dashboard.html",
        {
            "advisor": advisor
        }
    )

@login_required
def redirect_dashboard_view(request):

    if request.user.role == "advisor":

        return redirect("advisor_dashboard")

    return redirect("dashboard")
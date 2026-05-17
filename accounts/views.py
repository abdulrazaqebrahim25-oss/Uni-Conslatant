from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import StudentProfile, AdvisorProfile
from .forms import AdvisorProfileForm
from .forms import StudentProfileForm

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

@login_required
def advisor_profile_view(request):

    advisor = request.user.advisor_profile

    return render(
        request,
        "dashboard/advisor_profile.html",
        {
            "advisor": advisor
        }
    )

@login_required
def edit_advisor_profile_view(request):

    advisor = request.user.advisor_profile

    if request.method == "POST":

        form = AdvisorProfileForm(
            request.POST,
            instance=advisor
        )

        if form.is_valid():

            form.save()

            return redirect("advisor_profile")

    else:

        form = AdvisorProfileForm(instance=advisor)

    return render(
        request,
        "dashboard/edit_advisor_profile.html",
        {
            "form": form
        }
    )


@login_required
def edit_student_profile_view(request):

    student = request.user.student_profile

    if request.method == "POST":

        form = StudentProfileForm(
            request.POST,
            instance=student
        )

        if form.is_valid():

            form.save()

            return redirect("student_profile")

    else:

        form = StudentProfileForm(instance=student)

    return render(
        request,
        "dashboard/edit_student_profile.html",
        {
            "form": form
        }
    )
from django.shortcuts import render


from django.shortcuts import render, redirect

from .forms import RegisterForm
from .models import StudentProfile, AdvisorProfile

# Create your views here.
def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            if user.role == "student":

                StudentProfile.objects.create(
                    user=user
                )

            elif user.role == "advisor":

                AdvisorProfile.objects.create(
                    user=user
                )

            return redirect("login")

    else:

        form = RegisterForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form
        }
    )

from django.shortcuts import render


def login_view(request):

    return render(
        request,
        "registration/login.html"
    )
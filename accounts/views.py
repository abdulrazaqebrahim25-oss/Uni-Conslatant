from django.shortcuts import render, redirect

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


from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, StudentProfile, AdvisorProfile


class RegisterForm(UserCreationForm):

    ROLE_CHOICES = [
        ("student", "Student"),
        ("advisor", "Advisor"),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "role",
            "password1",
            "password2",
        ]
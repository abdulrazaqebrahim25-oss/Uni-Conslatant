from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from datetime import datetime

from .models import User, StudentProfile
from main_app.models import Major


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))

    major = forms.ModelChoiceField(
        queryset=Major.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"})
    )

    entry_year = forms.IntegerField(
        initial=datetime.now().year,
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    
    gpa = forms.DecimalField(
    required=False,
    max_digits=3,
    decimal_places=2,
    min_value=0.0,
    max_value=4.0
    )

    entry_semester = forms.ChoiceField(
        choices=StudentProfile.ENTRY_SEMESTER_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    preferred_semesters_per_year = forms.ChoiceField(
        choices=StudentProfile.SEMESTER_PREFERENCE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    budget_level = forms.ChoiceField(
        choices=StudentProfile.BUDGET_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    @transaction.atomic
    def save(self, commit=True):

        user = super().save(commit=False)
        user.role = "student"
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()

            student = StudentProfile.objects.create(
                user=user,
                major=self.cleaned_data["major"],
                entry_year=self.cleaned_data["entry_year"],
                entry_semester=self.cleaned_data["entry_semester"],
                preferred_semesters_per_year=self.cleaned_data["preferred_semesters_per_year"],
                budget_level=self.cleaned_data["budget_level"],
                gpa=self.cleaned_data.get("gpa")
            )

        return user
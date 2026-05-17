from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from datetime import datetime

from .models import User, StudentProfile, AdvisorProfile
from main_app.models import Major, Course


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    major = forms.ModelChoiceField(
        queryset=Major.objects.all(),
        widget=forms.Select(attrs={"class": "form-control", "id": "id_major"})
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
        max_value=4.0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 3.50"})
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

    # All courses — JS in the template filters by selected major visually.
    # Server-side we validate the selections belong to the chosen major.
    completed_courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Courses you have already completed"
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

    def clean(self):
        cleaned_data = super().clean()
        major = cleaned_data.get("major")
        courses = cleaned_data.get("completed_courses")

        # Validate that every ticked course actually belongs to the chosen major
        if major and courses:
            valid_ids = set(
                major.courses.values_list("id", flat=True)
            )
            invalid = [c.code for c in courses if c.id not in valid_ids]
            if invalid:
                raise forms.ValidationError(
                    f"These courses don't belong to your major: {', '.join(invalid)}"
                )

        return cleaned_data

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
                gpa=self.cleaned_data.get("gpa"),
            )

            # Save the ManyToMany completed courses
            completed = self.cleaned_data.get("completed_courses")
            if completed:
                student.completed_courses.set(completed)

        return user


class StudentProfileForm(forms.ModelForm):

    completed_courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),   # populated in __init__ based on major
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Completed Courses"
    )

    class Meta:
        model = StudentProfile
        fields = [
            "major",
            "gpa",
            "budget_level",
            "preferred_semesters_per_year",
            "completed_courses",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If the student already has a major, restrict the queryset to that major's courses
        if self.instance and self.instance.major_id:
            self.fields["completed_courses"].queryset = Course.objects.filter(
                majors=self.instance.major
            )
        else:
            self.fields["completed_courses"].queryset = Course.objects.all()


class AdvisorProfileForm(forms.ModelForm):

    class Meta:
        model = AdvisorProfile
        fields = ["office", "major"]
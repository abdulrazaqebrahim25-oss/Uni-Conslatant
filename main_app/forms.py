from django import forms
from .models import Major, Course


class StudentRegistrationForm(forms.form):
    name = forms.CharField(max_length=100, label="Full Name")
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    major = forms.ModelChoiceField(
        queryset = Major.objects.all(),
        label="Your Major",
        empty_label="-- Select your major --"
    )
    completed_courses = forms.ModelMultipleChoiceField(
        queryset = Course.objects.all(),
        widget = forms.CheckboxSelectMultiple,
        required=False, #a new student might have no prior courses
        label="Courses you have already completed (if any)"
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data
    
class LoginForm(forms.form):
    email = forms.EmailField(label="Emaill Address")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=100,
        required=True
    )

    last_name = forms.CharField(
        max_length=100,
        required=True
    )

    email = forms.EmailField(
        required=True
    )

    class Meta:

        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]

    def save(self, commit=True):

        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

        return user
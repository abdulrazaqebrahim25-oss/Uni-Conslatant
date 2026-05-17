from django import forms
from .models import Appointment
from django.utils import timezone


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment
        fields = ['advisor', 'start_time', 'end_time']

        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['start_time'].input_formats = (
            '%Y-%m-%dT%H:%M',
        )
        self.fields['end_time'].input_formats = (
            '%Y-%m-%dT%H:%M',
        )

   
    def clean_start_time(self):

        start_time = self.cleaned_data['start_time']

        if start_time < timezone.now():
            raise forms.ValidationError("You cannot select a past time.")

        return start_time

  
    def clean(self):

        cleaned_data = super().clean()

        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end:

            if end <= start:
                raise forms.ValidationError(
                    "End time must be after start time."
                )

        return cleaned_data
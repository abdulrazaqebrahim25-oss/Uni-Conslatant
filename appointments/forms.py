from django import forms
from .models import Appointment
from django.utils import timezone


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment
        fields = ['advisor', 'date']

        widgets = {
            'date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].input_formats = (
            '%Y-%m-%dT%H:%M',
        )


    def clean_date(self):

        date = self.cleaned_data['date']

        if date < timezone.now():
            raise forms.ValidationError("You cannot select a past date.")

        return date
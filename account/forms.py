# account/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import Student, User

class StudentLoginForm(forms.Form):
    index_number = forms.CharField(label='Index Number')
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        index_number = cleaned_data.get("index_number")
        password = cleaned_data.get("password")

        try:
            student = Student.objects.get(index_number=index_number)
            user = authenticate(username=student.user.email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid credentials")
            cleaned_data["user"] = user
        except Student.DoesNotExist:
            raise forms.ValidationError("Student not found")
        return cleaned_data


class StaffLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        user = authenticate(username=email, password=password)
        if user is None or not user.is_staff:
            raise forms.ValidationError("Invalid credentials or not a staff member")
        cleaned_data["user"] = user
        return cleaned_data

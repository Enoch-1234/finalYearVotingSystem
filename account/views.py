# account/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import StudentLoginForm, StaffLoginForm

def student_login_view(request):
    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("index")  # Or wherever students should go
    else:
        form = StudentLoginForm()
    return render(request, "student_login.html", {"form": form})


def staff_login_view(request):
    if request.method == "POST":
        form = StaffLoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("staff_dashboard")  # Or wherever staff should go
    else:
        form = StaffLoginForm()
    return render(request, "staff_login.html", {"form": form})


@login_required
def logout_view(request):
    """
    Logs out the user, clears session data, and redirects to the login page.
    """
    # Clear vote confirmation session data if it exists
    if 'vote_confirmation' in request.session:
        del request.session['vote_confirmation']
    if 'vote_confirmation_accessed' in request.session:
        del request.session['vote_confirmation_accessed']

    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('student_login')
# account/urls.py
from django.urls import path
from .views import student_login_view, staff_login_view, logout_view

urlpatterns = [
    path("login/student/", student_login_view, name="student_login"),
    path("login/staff/", staff_login_view, name="staff_login"),
    path('logout/', logout_view, name='logout'),
]

# account/backend.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from account.models import Student

User = get_user_model()

class StudentOrAdminAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if '@' in username:
                # Admin/staff login via email
                user = User.objects.get(email=username)
            else:
                # Student login via index_number
                student = Student.objects.select_related('user').get(index_number=username)
                user = student.user

            if user and user.check_password(password):
                return user
        except (User.DoesNotExist, Student.DoesNotExist):
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

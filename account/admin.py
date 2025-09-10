# account/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Student, Staff, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    model = Department

    list_display = ('name', )
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    search_fields = ('email',)
    ordering = ('email',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    model = Staff
    list_display = ('first_name', 'last_name', 'position')
    search_fields = ('first_name', 'last_name', 'position')
    exclude = ('user',)

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            # Create a consistent email address
            base_email = f"{obj.first_name.lower()}.{obj.last_name.lower()}@staffs.edu"
            counter = 1
            email = base_email

            # Ensure email uniqueness
            while User.objects.filter(email=email).exists():
                email = f"{obj.first_name.lower()}.{obj.last_name.lower()}{counter}@staffs.edu"
                counter += 1

            password = 'staffRanPass1234'
            user = User.objects.create_staff(email=email, password=password)
            obj.user = user

        super().save_model(request, obj, form, change)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    model = Student
    list_display = ('index_number', 'first_name', 'last_name', 'department', 'year_group')
    search_fields = ('index_number', 'first_name', 'last_name')
    list_filter = ('department', 'year_group')
    exclude = ('user',)

    def save_model(self, request, obj, form, change):
        if not obj.user_id:  # check user is not already set
            email = f"{obj.index_number.lower()}@students.edu"
            password = 'ranPass1234'
            user = User.objects.create_user(email=email, password=password, is_active=True)
            obj.user = user

        super().save_model(request, obj, form, change)




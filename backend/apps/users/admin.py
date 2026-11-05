from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "employee_code",
        "role",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "employee_code",
    )

    ordering = ("last_name", "first_name", "username")

    fieldsets = UserAdmin.fieldsets + (
        (
            "Información institucional",
            {
                "fields": (
                    "employee_code",
                    "role",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Información institucional",
            {"fields": ("email", "employee_code")},
        ),
    )
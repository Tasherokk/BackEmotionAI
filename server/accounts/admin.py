from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("id",)
    list_display = ("id", "username", "name","role", "company", "department", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "name", "company", "department")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "photo", "role", "company", "department")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "name", "photo", "role", "company", "department", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")

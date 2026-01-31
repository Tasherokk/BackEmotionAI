from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-date_joined",)
    list_display = ("id", "username", "name", "photo_preview", "role", "company", "department", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "company", "department", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "name", "company__name", "department__name")
    list_per_page = 25
    date_hierarchy = "date_joined"
    
    readonly_fields = ("photo_preview_large", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "photo", "photo_preview_large")}),
        (_("Organization"), {"fields": ("role", "company", "department")}),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",)
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "name", "photo", "role", "company", "department", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")
    
    def photo_preview(self, obj):
        """Миниатюра фото в списке"""
        if obj.photo:
            return format_html('<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 50%;" />', obj.photo.url)
        return "—"
    photo_preview.short_description = "Photo"
    
    def photo_preview_large(self, obj):
        """Превью фото в детальном просмотре"""
        if obj.photo:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />', obj.photo.url)
        return "No photo"
    photo_preview_large.short_description = "Photo Preview"
    
    actions = ["activate_users", "deactivate_users"]
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.")
    deactivate_users.short_description = "Deactivate selected users"


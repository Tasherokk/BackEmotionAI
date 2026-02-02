from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from .models import Company, Department, Event, Feedback


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "users_count", "departments_count", "events_count", "feedbacks_count")
    search_fields = ("name",)
    list_per_page = 25
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _users_count=Count("users", distinct=True),
            _departments_count=Count("departments", distinct=True),
            _events_count=Count("events", distinct=True),
            _feedbacks_count=Count("feedbacks", distinct=True),
        )
    
    def users_count(self, obj):
        return obj._users_count
    users_count.short_description = "Users"
    users_count.admin_order_field = "_users_count"
    
    def departments_count(self, obj):
        return obj._departments_count
    departments_count.short_description = "Departments"
    departments_count.admin_order_field = "_departments_count"
    
    def events_count(self, obj):
        return obj._events_count
    events_count.short_description = "Events"
    events_count.admin_order_field = "_events_count"
    
    def feedbacks_count(self, obj):
        return obj._feedbacks_count
    feedbacks_count.short_description = "Feedbacks"
    feedbacks_count.admin_order_field = "_feedbacks_count"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "users_count", "feedbacks_count")
    list_filter = ("company",)
    search_fields = ("name", "company__name")
    list_per_page = 25
    
    fieldsets = (
        (None, {"fields": ("company", "name")}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("company").annotate(
            _users_count=Count("users", distinct=True),
            _feedbacks_count=Count("feedbacks", distinct=True),
        )
    
    def users_count(self, obj):
        return obj._users_count
    users_count.short_description = "Users"
    users_count.admin_order_field = "_users_count"
    
    def feedbacks_count(self, obj):
        return obj._feedbacks_count
    feedbacks_count.short_description = "Feedbacks"
    feedbacks_count.admin_order_field = "_feedbacks_count"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "company", "local_starts_at", "local_ends_at", "safe_status", "safe_participants", "safe_feedbacks")
    list_filter = ("company", "starts_at")
    search_fields = ("title", "company__name")
    date_hierarchy = "starts_at"
    list_per_page = 25
    filter_horizontal = ("participants",)
    
    fieldsets = (
        (None, {"fields": ("company", "title")}),
        ("Schedule", {"fields": ("starts_at", "ends_at")}),
        ("Participants", {"fields": ("participants",)}),
    )
    
    def local_starts_at(self, obj):
        """Отображение времени начала в локальной timezone"""
        try:
            from django.utils import timezone
            import pytz
            
            if obj.starts_at:
                local_tz = pytz.timezone('Asia/Almaty')
                local_time = obj.starts_at.astimezone(local_tz)
                return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            return "—"
        except Exception as e:
            return f"Error: {str(e)}"
    local_starts_at.short_description = "Начало (Almaty)"
    local_starts_at.admin_order_field = "starts_at"
    
    def local_ends_at(self, obj):
        """Отображение времени окончания в локальной timezone"""
        try:
            from django.utils import timezone
            import pytz
            
            if obj.ends_at:
                local_tz = pytz.timezone('Asia/Almaty')
                local_time = obj.ends_at.astimezone(local_tz)
                return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            return "—"
        except Exception as e:
            return f"Error: {str(e)}"
    local_ends_at.short_description = "Окончание (Almaty)"
    local_ends_at.admin_order_field = "ends_at"
    
    def safe_status(self, obj):
        try:
            from django.utils import timezone
            now = timezone.now()
            
            if not obj.starts_at:
                return "—"
            
            if obj.ends_at and now > obj.ends_at:
                return mark_safe('<span style="color: #6c757d;">⬤ Завершено</span>')
            elif now >= obj.starts_at:
                return mark_safe('<span style="color: #28a745;">⬤ Активно</span>')
            else:
                return mark_safe('<span style="color: #007bff;">⬤ Предстоит</span>')
        except:
            return "—"
    safe_status.short_description = "Статус"
    
    def safe_participants(self, obj):
        try:
            count = obj.participants.all().count()
            return mark_safe(f'<span style="color: #17a2b8;">👥 {count}</span>')
        except:
            return "—"
    safe_participants.short_description = "Участники"
    
    def safe_feedbacks(self, obj):
        try:
            count = obj.feedbacks.all().count()
            color = "#28a745" if count > 0 else "#6c757d"
            return mark_safe(f'<span style="color: {color};">💬 {count}</span>')
        except:
            return "—"
    safe_feedbacks.short_description = "Отзывы"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "emotion", "company", "department", "event", "created_at")
    list_filter = ("emotion", "company", "department", "event", "created_at")
    search_fields = ("user__username", "user__name", "event__title", "company__name", "department__name")
    date_hierarchy = "created_at"
    list_per_page = 50
    readonly_fields = ("created_at", "emotion", "top3")
    
    fieldsets = (
        ("User Info", {"fields": ("user", "created_at")}),
        ("Emotion Analysis", {
            "fields": ("emotion", "top3"),
        }),
        ("Organization", {
            "fields": ("company", "department", "event"),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "company", "department", "event")


# Настройка главной страницы админки
admin.site.site_header = "Emotions AI Administration"
admin.site.site_title = "Emotions AI Admin"
admin.site.index_title = "Welcome to Emotions AI Admin Panel"

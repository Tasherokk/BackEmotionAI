from django.contrib import admin
from django.utils.html import format_html
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
    list_display = ("id", "title", "company", "starts_at", "ends_at", "status", "participants_count", "feedbacks_count")
    list_filter = ("company", "starts_at", "ends_at")
    search_fields = ("title", "company__name")
    date_hierarchy = "starts_at"
    list_per_page = 25
    filter_horizontal = ("participants",)
    
    fieldsets = (
        (None, {"fields": ("company", "title")}),
        ("Schedule", {"fields": ("starts_at", "ends_at")}),
        ("Participants", {"fields": ("participants",)}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        try:
            return qs.select_related("company").prefetch_related("participants").annotate(
                _feedbacks_count=Count("feedbacks", distinct=True),
            )
        except Exception as e:
            import traceback
            print(f"ERROR in EventAdmin.get_queryset: {e}")
            print(traceback.format_exc())
            return qs
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Фильтруем участников только по компании события"""
        if db_field.name == "participants":
            # Получаем ID события из URL
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    event = Event.objects.get(pk=obj_id)
                    # Показываем только сотрудников этой компании
                    from accounts.models import User
                    kwargs["queryset"] = User.objects.filter(
                        company=event.company, 
                        role=User.Role.EMPLOYEE
                    )
                except Event.DoesNotExist:
                    pass
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def status(self, obj):
        """Статус события"""
        from django.utils import timezone
        now = timezone.now()
        
        if obj.ends_at and now > obj.ends_at:
            return format_html('<span style="color: gray;">● Finished</span>')
        elif now >= obj.starts_at:
            return format_html('<span style="color: green;">● Active</span>')
        else:
            return format_html('<span style="color: blue;">● Upcoming</span>')
    status.short_description = "Status"
    
    def participants_count(self, obj):
        try:
            return obj.participants.count()
        except Exception as e:
            print(f"ERROR in participants_count: {e}")
            return 0
    participants_count.short_description = "Participants"
    
    def feedbacks_count(self, obj):
        try:
            return obj._feedbacks_count
        except AttributeError:
            print(f"ERROR: obj._feedbacks_count not found for {obj}")
            return obj.feedbacks.count()
    feedbacks_count.short_description = "Feedbacks"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "emotion_badge", "company", "department", "event", "created_at")
    list_filter = ("emotion", "company", "department", "event", "created_at")
    search_fields = ("user__username", "user__name", "event__title", "company__name", "department__name")
    date_hierarchy = "created_at"
    list_per_page = 50
    readonly_fields = ("created_at", "top3_display")
    
    fieldsets = (
        ("User Info", {"fields": ("user", "created_at")}),
        ("Emotion Analysis", {
            "fields": ("emotion", "top3_display"),
        }),
        ("Organization", {
            "fields": ("company", "department", "event"),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "company", "department", "event")
    
    def emotion_badge(self, obj):
        """Эмоция с цветовой меткой"""
        colors = {
            "happy": "#4CAF50",
            "sad": "#2196F3",
            "angry": "#F44336",
            "surprised": "#FF9800",
            "fear": "#9C27B0",
            "neutral": "#607D8B",
        }
        color = colors.get(obj.emotion.lower(), "#757575")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color, obj.emotion.upper()
        )
    emotion_badge.short_description = "Emotion"
    emotion_badge.admin_order_field = "emotion"
    
    def top3_display(self, obj):
        """Топ-3 эмоций"""
        if obj.top3:
            items = "<br>".join([f"{i+1}. {em}" for i, em in enumerate(obj.top3)])
            return format_html('<div style="line-height: 1.8;">{}</div>', items)
        return "—"
    top3_display.short_description = "Top 3 Emotions"


# Настройка главной страницы админки
admin.site.site_header = "Emotions AI Administration"
admin.site.site_title = "Emotions AI Admin"
admin.site.index_title = "Welcome to Emotions AI Admin Panel"

admin.site.site_title = "Emotions AI Admin"
admin.site.index_title = "Welcome to Emotions AI Admin Panel"


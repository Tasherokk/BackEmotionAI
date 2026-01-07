from django.contrib import admin
from .models import Company, Department, Event, Feedback

admin.site.register(Company)
admin.site.register(Department)
admin.site.register(Event)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company", "department", "event", "emotion", "confidence", "created_at")
    list_filter = ("company", "department", "emotion")
    search_fields = ("user__username", "user__name", "event__title")

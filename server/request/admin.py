from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count
from .models import RequestType, Request, RequestMessage


@admin.register(RequestType)
class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description_short", "requests_count"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    
    def description_short(self, obj):
        """Сокращенное описание"""
        if len(obj.description) > 100:
            return f"{obj.description[:100]}..."
        return obj.description
    description_short.short_description = "Description"
    
    def requests_count(self, obj):
        """Количество заявок этого типа"""
        count = obj.requests.count()
        return format_html(
            '<span style="background: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    requests_count.short_description = "Total Requests"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(request_count=Count('requests'))


class RequestMessageInline(admin.TabularInline):
    model = RequestMessage
    extra = 0
    readonly_fields = ["sender_info", "text", "file_link", "created_at"]
    fields = ["created_at", "sender_info", "text", "file_link"]
    can_delete = False
    ordering = ["created_at"]
    
    def sender_info(self, obj):
        """Информация об отправителе с ролью"""
        try:
            if not obj.sender:
                return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.sender_id)
            role_colors = {
                "HR": "#2196F3",
                "EMPLOYEE": "#FF9800"
            }
            color = role_colors.get(obj.sender.role, "#666")
            return format_html(
                '<strong style="color: {};">{}</strong> ({})',
                color,
                obj.sender.name or obj.sender.username,
                obj.sender.role
            )
        except Exception:
            return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.sender_id)
    sender_info.short_description = "Sender"
    
    def file_link(self, obj):
        """Ссылка на файл"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #4CAF50;">📎 {}</a>',
                obj.file.url,
                obj.file.name.split('/')[-1]
            )
        return mark_safe('<span style="color: #999;">No file</span>')
    file_link.short_description = "Attached File"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = [
        "id", 
        "colored_status", 
        "type_info", 
        "employee_info", 
        "hr_info", 
        "messages_count",
        "created_at",
        "duration_info"
    ]
    list_filter = ["status", "type", "created_at", "employee__company"]
    search_fields = [
        "employee__username", 
        "employee__name",
        "hr__username", 
        "hr__name",
        "type__name"
    ]
    readonly_fields = ["created_at", "closed_at", "request_summary"]
    inlines = [RequestMessageInline]
    list_per_page = 25
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("📋 Request Information", {
            "fields": ("type", "status", "request_summary")
        }),
        ("👥 Participants", {
            "fields": ("employee", "hr")
        }),
        ("🕒 Timeline", {
            "fields": ("created_at", "closed_at")
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Фильтрация пользователей по ролям"""
        from accounts.models import User
        
        if db_field.name == "employee":
            kwargs["queryset"] = User.objects.filter(role=User.Role.EMPLOYEE, is_active=True)
        elif db_field.name == "hr":
            kwargs["queryset"] = User.objects.filter(role=User.Role.HR, is_active=True)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def colored_status(self, obj):
        """Статус с цветным фоном"""
        colors = {
            "OPEN": "#FF9800",
            "IN_PROGRESS": "#2196F3",
            "CLOSED": "#4CAF50"
        }
        color = colors.get(obj.status, "#999")
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = "Status"
    colored_status.admin_order_field = "status"
    
    def type_info(self, obj):
        """Информация о типе заявки"""
        return format_html(
            '<strong>{}</strong><br><small style="color: #666;">{}</small>',
            obj.type.name,
            obj.type.description[:50] + "..." if len(obj.type.description) > 50 else obj.type.description
        )
    type_info.short_description = "Type"
    
    def employee_info(self, obj):
        """Информация о сотруднике"""
        try:
            if not obj.employee:
                return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.employee_id)
            url = reverse("admin:accounts_user_change", args=[obj.employee.id])
            return format_html(
                '<a href="{}" style="color: #FF9800; font-weight: bold;">👤 {}</a><br>'
                '<small style="color: #666;">{}</small>',
                url,
                obj.employee.name or obj.employee.username,
                obj.employee.department.name if obj.employee.department else "No dept"
            )
        except Exception:
            return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.employee_id)
    employee_info.short_description = "Employee"
    
    def hr_info(self, obj):
        """Информация об HR"""
        try:
            if not obj.hr:
                return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.hr_id)
            url = reverse("admin:accounts_user_change", args=[obj.hr.id])
            return format_html(
                '<a href="{}" style="color: #2196F3; font-weight: bold;">🎯 {}</a><br>'
                '<small style="color: #666;">{}</small>',
                url,
                obj.hr.name or obj.hr.username,
                obj.hr.company.name if obj.hr.company else "No company"
            )
        except Exception:
            return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.hr_id)
    hr_info.short_description = "Assigned HR"
    
    def messages_count(self, obj):
        """Количество сообщений"""
        count = obj.messages.count()
        return format_html(
            '<span style="background: #E3F2FD; color: #1976D2; padding: 3px 8px; border-radius: 3px; font-weight: bold;">💬 {}</span>',
            count
        )
    messages_count.short_description = "Messages"
    
    def duration_info(self, obj):
        """Длительность обработки"""
        from django.utils import timezone
        
        if obj.status == Request.Status.CLOSED and obj.closed_at:
            duration = obj.closed_at - obj.created_at
            days = duration.days
            hours = duration.seconds // 3600
            
            if days > 0:
                text = f"{days}d {hours}h"
                color = "#4CAF50" if days < 3 else "#FF9800" if days < 7 else "#F44336"
            else:
                text = f"{hours}h"
                color = "#4CAF50"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">⏱️ {}</span>',
                color, text
            )
        elif obj.status != Request.Status.CLOSED:
            duration = timezone.now() - obj.created_at
            days = duration.days
            color = "#4CAF50" if days < 3 else "#FF9800" if days < 7 else "#F44336"
            return format_html(
                '<span style="color: {}; font-weight: bold;">⏳ {}d (open)</span>',
                color, days
            )
        return mark_safe('<span style="color: #999;">-</span>')
    duration_info.short_description = "Duration"
    
    def request_summary(self, obj):
        """Краткая информация о заявке"""
        messages = obj.messages.all().order_by("created_at")
        first_message = messages.first()
        
        # Безопасное получение информации о пользователях
        try:
            employee_name = obj.employee.name or obj.employee.username if obj.employee else f"Deleted (ID: {obj.employee_id})"
            employee_username = obj.employee.username if obj.employee else "—"
        except Exception:
            employee_name = f"Deleted (ID: {obj.employee_id})"
            employee_username = "—"
        
        try:
            hr_name = obj.hr.name or obj.hr.username if obj.hr else f"Deleted (ID: {obj.hr_id})"
            hr_username = obj.hr.username if obj.hr else "—"
        except Exception:
            hr_name = f"Deleted (ID: {obj.hr_id})"
            hr_username = "—"
        
        summary = format_html(
            '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; border-left: 4px solid #2196F3;">'
            '<p><strong>Request #{}</strong></p>'
            '<p><strong>Type:</strong> {}</p>'
            '<p><strong>Status:</strong> <span style="color: {};">{}</span></p>'
            '<p><strong>Employee:</strong> {} ({})</p>'
            '<p><strong>Assigned HR:</strong> {} ({})</p>'
            '<p><strong>Created:</strong> {}</p>',
            obj.id,
            obj.type.name,
            {"OPEN": "#FF9800", "IN_PROGRESS": "#2196F3", "CLOSED": "#4CAF50"}.get(obj.status, "#999"),
            obj.get_status_display(),
            employee_name,
            employee_username,
            hr_name,
            hr_username,
            obj.created_at.strftime("%Y-%m-%d %H:%M")
        )
        
        if obj.closed_at:
            summary += format_html(
                '<p><strong>Closed:</strong> {}</p>',
                obj.closed_at.strftime("%Y-%m-%d %H:%M")
            )
        
        if first_message:
            summary += format_html(
                '<p style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">'
                '<strong>Initial Message:</strong><br>'
                '<em style="color: #666;">{}</em></p>',
                first_message.text[:200] + "..." if len(first_message.text) > 200 else first_message.text
            )
        
        summary += mark_safe('</div>')
        return summary
    request_summary.short_description = "Summary"


@admin.register(RequestMessage)
class RequestMessageAdmin(admin.ModelAdmin):
    list_display = [
        "id", 
        "request_link", 
        "sender_info", 
        "text_preview", 
        "has_file",
        "created_at"
    ]
    list_filter = ["created_at", "sender__role"]
    search_fields = ["text", "sender__username", "request__id"]
    readonly_fields = ["request", "sender", "text", "file", "created_at"]
    list_per_page = 50
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Message Info", {
            "fields": ("request", "sender", "created_at")
        }),
        ("Content", {
            "fields": ("text", "file")
        }),
    )
    
    def request_link(self, obj):
        """Ссылка на заявку"""
        url = reverse("admin:request_request_change", args=[obj.request.id])
        return format_html(
            '<a href="{}" style="font-weight: bold;">Request #{}</a><br>'
            '<small style="color: #666;">{}</small>',
            url,
            obj.request.id,
            obj.request.type.name
        )
    request_link.short_description = "Request"
    
    def sender_info(self, obj):
        """Информация об отправителе"""
        try:
            if not obj.sender:
                return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.sender_id)
            role_colors = {
                "HR": "#2196F3",
                "EMPLOYEE": "#FF9800"
            }
            color = role_colors.get(obj.sender.role, "#666")
            url = reverse("admin:accounts_user_change", args=[obj.sender.id])
            return format_html(
                '<a href="{}" style="color: {}; font-weight: bold;">{}</a><br>'
                '<small>{}</small>',
                url,
                color,
                obj.sender.name or obj.sender.username,
                obj.sender.role
            )
        except Exception:
            return format_html('<span style="color: red;">🚨 Deleted (ID: {})</span>', obj.sender_id)
    sender_info.short_description = "Sender"
    
    def text_preview(self, obj):
        """Предпросмотр текста"""
        if len(obj.text) > 100:
            return format_html(
                '<span title="{}">{}</span>',
                obj.text,
                obj.text[:100] + "..."
            )
        return obj.text
    text_preview.short_description = "Message"
    
    def has_file(self, obj):
        """Наличие файла"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #4CAF50; font-size: 18px;">📎</a>',
                obj.file.url
            )
        return mark_safe('<span style="color: #ccc;">-</span>')
    has_file.short_description = "File"
    
    def has_add_permission(self, request):
        return False
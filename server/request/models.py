from django.db import models
from django.conf import settings


class RequestType(models.Model):
    """Тип заявки - общий для всех компаний, создается в админке"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = "Request Type"
        verbose_name_plural = "Request Types"

    def __str__(self):
        return self.name


class Request(models.Model):
    """Заявка от employee к HR"""
    
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        CLOSED = "CLOSED", "Closed"

    type = models.ForeignKey(
        RequestType,
        on_delete=models.PROTECT,
        related_name="requests"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_requests"
    )
    hr = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hr_requests"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["hr", "status"]),
        ]

    def __str__(self):
        return f"Request #{self.id} - {self.type.name} ({self.employee.username} -> {self.hr.username})"


class RequestMessage(models.Model):
    """Сообщение в заявке"""
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    text = models.TextField()
    file = models.FileField(upload_to="request_files/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message in Request #{self.request.id} by {self.sender.username}"
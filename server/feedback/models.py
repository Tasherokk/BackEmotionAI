from django.db import models
from django.conf import settings

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return f"{self.company.name} — {self.name}"


class Event(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="events", blank=True)

    def __str__(self):
        return f"{self.company.name} — {self.title}"


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    created_at = models.DateTimeField(auto_now_add=True)

    # результат модели
    emotion = models.CharField(max_length=32)
    top3 = models.JSONField(null=True, blank=True)

    # аналитика
    company = models.ForeignKey(Company, on_delete=models.PROTECT, null=True, blank=True, related_name="feedbacks")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True, related_name="feedbacks")
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedbacks")

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["emotion"]),
        ]

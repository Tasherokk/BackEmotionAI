from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


from django.conf import settings
from django.db import models

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    created_at = models.DateTimeField(auto_now_add=True)

    # результат модели
    emotion = models.CharField(max_length=32)          # "angry"
    confidence = models.FloatField()                   # 0.99

    probs = models.JSONField()                         # {"angry":0.99,...}
    top3 = models.JSONField(null=True, blank=True)     # [{"label":"angry","prob":...}, ...]
    face_box = models.JSONField(null=True, blank=True) # {"x1":..,"y1":..,"x2":..,"y2":..}

    # для будущей аналитики
    department = models.CharField(max_length=255, blank=True, default="")  # пока строкой, без сильных изменений
    event_id = models.IntegerField(null=True, blank=True)       
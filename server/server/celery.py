import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = Celery('server')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Настройки для задач
app.conf.update(
    task_soft_time_limit=120,  # Мягкий лимит (предупреждение)
    task_time_limit=180,       # Жесткий лимит (принудительное завершение)
    task_acks_late=True,       # Подтверждать задачу после выполнения
    worker_prefetch_multiplier=1,  # Брать по одной задаче за раз
)

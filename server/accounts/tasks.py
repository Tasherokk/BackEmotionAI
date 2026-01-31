from celery import shared_task
from django.core.files.base import ContentFile
from feedback.models import Feedback
from feedback.services.emotion_ai import analyze_face
import io


@shared_task
def process_photo_login_feedback(user_id, photo_data):
    """
    Обработка фото после успешной авторизации:
    1. Анализ эмоций через AI
    2. Создание feedback с event_id=None
    """
    from accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Преобразуем bytes обратно в file-like объект
        photo_file = ContentFile(photo_data, name='photo_login.jpg')
        
        # Анализ эмоций через AI
        ai_result = analyze_face(photo_file)
        
        # Создаем feedback без привязки к событию
        feedback = Feedback.objects.create(
            user=user,
            emotion=ai_result.get("emotion", "unknown"),
            top3=ai_result.get("top3", []),
            event_id=None,  # Без привязки к событию
            company=user.company,
            department=user.department,
        )
        
        return {
            "success": True,
            "feedback_id": feedback.id,
            "emotion": feedback.emotion
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

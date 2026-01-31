from celery import shared_task
from django.core.files.uploadedfile import InMemoryUploadedFile
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
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting feedback processing for user_id={user_id}, photo_size={len(photo_data)}")
        
        user = User.objects.get(id=user_id)
        logger.info(f"User found: {user.username}")
        
        # Создаем InMemoryUploadedFile из bytes для совместимости с analyze_face
        photo_file = InMemoryUploadedFile(
            file=io.BytesIO(photo_data),
            field_name='photo',
            name='photo_login.jpg',
            content_type='image/jpeg',
            size=len(photo_data),
            charset=None
        )
        
        logger.info("Calling analyze_face...")
        # Анализ эмоций через AI
        ai_result = analyze_face(photo_file)
        logger.info(f"AI result: {ai_result}")
        
        # Создаем feedback без привязки к событию
        feedback = Feedback.objects.create(
            user=user,
            emotion=ai_result.get("emotion", "unknown"),
            top3=ai_result.get("top3", []),
            event_id=None,  # Без привязки к событию
            company=user.company,
            department=user.department,
        )
        
        logger.info(f"Feedback created: id={feedback.id}")
        
        return {
            "success": True,
            "feedback_id": feedback.id,
            "emotion": feedback.emotion
        }
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

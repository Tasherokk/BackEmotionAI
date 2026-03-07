import requests
import os
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)
AI_BASE_URL = os.environ["AI_BASE_URL"]

# Максимальный размер стороны фото для нормализации
MAX_IMAGE_SIZE = 1024
JPEG_QUALITY = 90


class AIClientError(Exception):
    """Raised when AI service returns 4xx (bad input, no face detected, etc.)"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _normalize_photo(raw_bytes: bytes) -> bytes:
    """
    Нормализует фото: ресайз до MAX_IMAGE_SIZE по большей стороне,
    конвертация в RGB JPEG. Это обеспечивает одинаковый формат и размер
    для обоих фото при сравнении, улучшая качество распознавания.
    """
    img = Image.open(io.BytesIO(raw_bytes))

    # Исправляем ориентацию по EXIF (камера телефона часто ставит rotation в EXIF)
    try:
        from PIL import ExifTags
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == 'Orientation':
                    if value == 3:
                        img = img.rotate(180, expand=True)
                    elif value == 6:
                        img = img.rotate(270, expand=True)
                    elif value == 8:
                        img = img.rotate(90, expand=True)
                    break
    except Exception:
        pass

    img = img.convert("RGB")

    # Ресайз с сохранением пропорций
    w, h = img.size
    if max(w, h) > MAX_IMAGE_SIZE:
        if w > h:
            new_w = MAX_IMAGE_SIZE
            new_h = int(h * MAX_IMAGE_SIZE / w)
        else:
            new_h = MAX_IMAGE_SIZE
            new_w = int(w * MAX_IMAGE_SIZE / h)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        logger.debug(f"Resized photo from {w}x{h} to {new_w}x{new_h}")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def verify_face_authorization(stored_photo_field, uploaded_photo_file) -> dict:
    """
    Verifies if two photos match using AI face recognition service.
    
    Args:
        stored_photo_field: Django ImageField from User model
        uploaded_photo_file: Uploaded file from request
    
    Returns:
        dict with keys: verdict, similarity, similarity_percent, etc.
    
    Raises:
        AIClientError: If AI service returns 4xx (e.g. no face detected)
        requests.Timeout: If AI service doesn't respond within timeout
        requests.RequestException: For other request errors (5xx, connection, etc.)
    """
    try:
        # Read uploaded photo
        uploaded_content = uploaded_photo_file.read()
        uploaded_photo_file.seek(0)
        
        # Read stored photo
        stored_photo_field.open('rb')
        stored_content = stored_photo_field.read()
        stored_photo_field.close()
        
        # Нормализуем оба фото (ресайз + EXIF ориентация + JPEG)
        stored_content = _normalize_photo(stored_content)
        uploaded_content = _normalize_photo(uploaded_content)
        
        logger.info(f"Normalized photos: stored={len(stored_content)} bytes, uploaded={len(uploaded_content)} bytes")
        
        # Prepare files for authorization endpoint
        files = {
            'photo1': (stored_photo_field.name, stored_content, 'image/jpeg'),
            'photo2': (uploaded_photo_file.name, uploaded_content, 'image/jpeg')
        }
        
        # Timeout 45 секунд - достаточно для AI обработки, но меньше Gunicorn timeout (300s)
        r = requests.post(f"{AI_BASE_URL}/authorization", files=files, timeout=45)
        
        # Separate 4xx (client/input errors) from 5xx (server errors)
        if 400 <= r.status_code < 500:
            try:
                detail = r.json().get('detail', r.text)
            except Exception:
                detail = r.text
            logger.warning(f"AI service returned {r.status_code}: {detail}")
            raise AIClientError(r.status_code, detail)
        
        r.raise_for_status()
        return r.json()
    
    except AIClientError:
        raise
    except requests.Timeout:
        logger.error(f"AI service timeout for authorization endpoint")
        raise
    except requests.RequestException as e:
        logger.error(f"AI service request failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in face authorization: {str(e)}")
        raise

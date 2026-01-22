import requests
import os

AI_BASE_URL = os.environ["AI_BASE_URL"]


def verify_face_authorization(stored_photo_field, uploaded_photo_file) -> dict:
    """
    Verifies if two photos match using AI face recognition service.
    
    Args:
        stored_photo_field: Django ImageField from User model
        uploaded_photo_file: Uploaded file from request
    
    Returns:
        dict with keys: verdict, similarity, similarity_percent, etc.
    """
    # Read uploaded photo
    uploaded_content = uploaded_photo_file.read()
    uploaded_photo_file.seek(0)
    
    # Read stored photo
    stored_photo_field.open('rb')
    stored_content = stored_photo_field.read()
    stored_photo_field.close()
    
    # Prepare files for authorization endpoint
    files = {
        'photo1': (stored_photo_field.name, stored_content, 'image/jpeg'),
        'photo2': (uploaded_photo_file.name, uploaded_content, uploaded_photo_file.content_type or 'image/jpeg')
    }
    
    r = requests.post(f"{AI_BASE_URL}/authorization", files=files, timeout=60)
    r.raise_for_status()
    return r.json()

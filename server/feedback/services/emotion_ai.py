import requests
import os
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)
AI_BASE_URL = os.environ["AI_BASE_URL"]

def analyze_face(image_file) -> dict:
    """
    Analyze face emotions using AI service.
    
    Raises:
        requests.Timeout: If AI service doesn't respond within timeout
        requests.RequestException: For other request errors
        Exception: For image processing errors
    """
    try:
        logger.info(f"Starting face analysis, AI_BASE_URL: {AI_BASE_URL}")
        
        # Read image
        content = image_file.read()
        image_file.seek(0)
        
        # Compress large images to avoid connection issues
        img = Image.open(BytesIO(content))
        logger.info(f"Image size: {img.size}, mode: {img.mode}")
        
        # Resize if image is too large (max 1024px on longest side)
        max_size = 4096
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Image resized to: {new_size}")
        
        # Convert to JPEG with quality 85 to reduce size
        buffer = BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=85)
        compressed_content = buffer.getvalue()
        logger.info(f"Compressed image size: {len(compressed_content)} bytes")
        
        files = {
            "file": (image_file.name, compressed_content, "image/jpeg")
        }

        logger.info(f"Sending request to {AI_BASE_URL}/predict")
        r = requests.post(f"{AI_BASE_URL}/predict", files=files, timeout=120)
        r.raise_for_status()
        result = r.json()
        logger.info(f"AI response: {result}")
        return result
    
    except requests.Timeout:
        logger.error(f"AI service timeout: {AI_BASE_URL}/predict")
        raise
    except requests.RequestException as e:
        logger.error(f"AI service request failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in analyze_face: {str(e)}", exc_info=True)
        raise

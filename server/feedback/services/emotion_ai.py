import requests
import os
import logging

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
        
        # Read original uploaded image without modifying it
        content = image_file.read()
        image_file.seek(0)
        logger.info(f"Original image size: {len(content)} bytes")
        
        files = {
            "file": (image_file.name, content, getattr(image_file, "content_type", "application/octet-stream"))
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

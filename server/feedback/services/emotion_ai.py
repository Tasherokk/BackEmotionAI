import requests
import os

AI_BASE_URL = os.environ["AI_BASE_URL"]

def analyze_face(image_file) -> dict:
    content = image_file.read()
    image_file.seek(0)

    files = {
        "file": (image_file.name, content, image_file.content_type or "image/jpeg")
    }

    r = requests.post(f"{AI_BASE_URL}/predict", files=files, timeout=60)
    r.raise_for_status()
    return r.json()

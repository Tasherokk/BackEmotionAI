import requests
import os
from PIL import Image
from io import BytesIO

AI_BASE_URL = os.environ["AI_BASE_URL"]

def analyze_face(image_file) -> dict:
    # Read image
    content = image_file.read()
    image_file.seek(0)
    
    # Compress large images to avoid connection issues
    img = Image.open(BytesIO(content))
    
    # Resize if image is too large (max 1024px on longest side)
    max_size = 1024
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to JPEG with quality 85 to reduce size
    buffer = BytesIO()
    img.convert('RGB').save(buffer, format='JPEG', quality=85)
    compressed_content = buffer.getvalue()
    
    files = {
        "file": (image_file.name, compressed_content, "image/jpeg")
    }

    r = requests.post(f"{AI_BASE_URL}/predict", files=files, timeout=60)
    r.raise_for_status()
    return r.json()

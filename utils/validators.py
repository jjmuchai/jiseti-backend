# utils/validators.py
import re
from urllib.parse import urlparse

def validate_email(email):
    """Validate email format - Gmail only as per requirements"""
    if not email:
        return False
    
    # Gmail validation pattern
    gmail_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return re.match(gmail_pattern, email) is not None

def validate_media_url(url, media_type=None):
    """Validate media URL format and accessibility"""
    if not url:
        return True  # Empty URLs are allowed
    
    try:
        # Basic URL validation
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        
        if result.scheme not in ['http', 'https']:
            return False
        
        # Media type specific validation
        if media_type:
            url_lower = url.lower()
            
            if media_type == 'image':
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
                if not any(url_lower.endswith(ext) for ext in image_extensions):
                    return False
            
            elif media_type == 'video':
                video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
                if not any(url_lower.endswith(ext) for ext in video_extensions):
                    return False
        
        return True
        
    except Exception:
        return False

def validate_coordinates(latitude, longitude):
    """Validate GPS coordinates"""
    try:
        if latitude is None or longitude is None:
            return True  # Allow empty coordinates
        
        lat = float(latitude)
        lng = float(longitude)
        
        # Check coordinate ranges
        if not (-90 <= lat <= 90):
            return False
        if not (-180 <= lng <= 180):
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False

def validate_phone_number(phone):
    """Validate phone number format (basic validation)"""
    if not phone:
        return True  # Phone is optional
    
    # Remove spaces and common separators
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Basic phone validation (digits and + sign)
    phone_pattern = r'^\+?[0-9]{10,15}$'
    return re.match(phone_pattern, clean_phone) is not None

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    return True, "Password is valid"

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return text
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>\"\'%;()&+]', '', text)
    return text.strip()

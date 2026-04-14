# helpers.py - Shared utility functions used across the app

import os
import uuid
from typing import Optional
from werkzeug.utils import secure_filename


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if an uploaded filename has an allowed extension.
    
    Security note: We check BOTH that there's a dot AND the extension is allowed.
    This prevents files like "resume" (no extension) or "resume.exe" from uploading.
    """
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def save_uploaded_file(file, upload_folder: str, allowed_extensions: set) -> Optional[str]:
    """
    Safely save an uploaded file to disk.
    
    Steps:
    1. Check it's an allowed type
    2. Sanitize the filename (remove special characters)
    3. Add a unique ID prefix (prevents overwriting files with same name)
    4. Save to upload folder
    
    Returns: Full path to saved file, or None if invalid
    """
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename, allowed_extensions):
        return None
    
    # secure_filename removes dangerous characters like "../" that could 
    # allow attackers to save files outside the upload folder
    safe_name = secure_filename(file.filename)
    
    # Add UUID prefix to avoid filename collisions
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    
    # Create upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)
    
    return file_path


def format_skills_for_display(skills_dict: dict) -> dict:
    """
    Format skills dictionary for JSON response / display.
    Removes the 'all' key and formats categories nicely.
    """
    display = {}
    category_labels = {
        'programming_languages': '💻 Programming Languages',
        'web_technologies': '🌐 Web Technologies',
        'databases': '🗄️ Databases',
        'cloud_devops': '☁️ Cloud & DevOps',
        'data_science_ml': '🤖 Data Science & ML',
        'tools_practices': '🛠️ Tools & Practices',
        'soft_skills': '🤝 Soft Skills',
    }
    
    for category, skills in skills_dict.items():
        if category == 'all':
            continue
        label = category_labels.get(category, category.replace('_', ' ').title())
        display[label] = skills
    
    return display


def cleanup_file(file_path: str) -> None:
    """Delete a file from disk (used to clean up uploaded files after processing)."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Silent fail - cleanup is best-effort


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate long text for display purposes."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

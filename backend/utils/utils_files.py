# backend/utils/validators.py
"""
Input validation utilities
"""

from fastapi import UploadFile, HTTPException


# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/gif',
    'application/pdf',
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 
    'audio/mp4', 'audio/x-m4a', 'audio/ogg'
}


def validate_file_size(file: UploadFile) -> None:
    """
    Validate file size
    
    Args:
        file: Uploaded file
    
    Raises:
        HTTPException if file is too large
    """
    # Read file to check size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum allowed size (10MB)"
        )


def validate_file_type(file: UploadFile) -> None:
    """
    Validate file type
    
    Args:
        file: Uploaded file
    
    Raises:
        HTTPException if file type is not allowed
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{file.content_type}' is not supported. Allowed types: images, PDFs, and audio files."
        )


def validate_text_input(text: str, min_length: int = 0, max_length: int = 50000) -> None:
    """
    Validate text input
    
    Args:
        text: Input text
        min_length: Minimum required length
        max_length: Maximum allowed length
    
    Raises:
        HTTPException if validation fails
    """
    if len(text) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text input is too short. Minimum length: {min_length} characters"
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text input is too long. Maximum length: {max_length} characters"
        )


# backend/utils/logger.py
"""
Logging configuration
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with console and optional file output
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
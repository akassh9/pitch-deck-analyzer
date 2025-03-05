"""
Centralized configuration management for the application.
This module loads configuration from environment variables and provides
a single source of truth for all configuration values.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """Central configuration class for the application."""
    
    # API Keys
    HF_API_KEY = os.getenv("HF_API_KEY")
    GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Application settings
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1")
    DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "False").lower() in ("true", "1")
    
    # Redis settings
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # File storage
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BACKEND_DIR, "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB default
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    @classmethod
    def configure_logging(cls):
        """Configure logging based on the configuration."""
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required_keys = [
            "HF_API_KEY", 
            "GOOGLE_API_KEY", 
            "GOOGLE_CSE_ID", 
            "GROQ_API_KEY"
        ]
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
        
        return True 
# backend/config.py
import os
from dotenv import load_dotenv

# Load environment variables once at startup.
load_dotenv()

class Config:
    HF_API_KEY = os.getenv("HF_API_KEY")
    GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "False").lower() in ("true", "1")

def validate_config():
    missing = []
    if not Config.HF_API_KEY:
        missing.append("HF_API_KEY")
    if not Config.GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY")
    if not Config.GOOGLE_CSE_ID:
        missing.append("GOOGLE_CSE_ID")
    # Add more validations here if needed.
    if missing:
        raise RuntimeError(f"Missing required environment variable(s): {', '.join(missing)}")

# Validate configuration immediately.
validate_config()
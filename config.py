import os
from pathlib import Path
from dotenv import load_dotenv

# Load from .env if present
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
PRESETS_DIR = STATIC_DIR / "presets"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "Kore").strip()
PORT = int(os.getenv("PORT", 8000))

# Current Recommended Gemini Models
VISION_MODEL = "gemini-3.8-flash"
CONVERSE_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.1-flash-tts-preview"


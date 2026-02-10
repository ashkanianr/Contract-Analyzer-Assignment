"""Backend configuration from environment and .env file."""
import os
from pathlib import Path

# Project root (parent of backend/)
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env from project root so API keys can be set there
def _load_dotenv():
    try:
        from dotenv import load_dotenv
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

_load_dotenv()

# LLM — defaults set to Gemini 3 Flash Preview
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
LLM_PRIMARY: str = os.environ.get("LLM_PRIMARY", "google").lower()
LLM_MODEL_GOOGLE: str = os.environ.get("LLM_MODEL_GOOGLE", "gemini-3-flash-preview")
LLM_MODEL_OPENROUTER: str = os.environ.get(
    "LLM_MODEL_OPENROUTER", "google/gemini-3-flash-preview"
)

# API
API_PREFIX = "/api"

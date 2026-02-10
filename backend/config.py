"""Backend configuration from environment."""
import os
from pathlib import Path

# Project root (parent of backend/)
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# LLM
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
LLM_PRIMARY: str = os.environ.get("LLM_PRIMARY", "google").lower()
LLM_MODEL_GOOGLE: str = os.environ.get("LLM_MODEL_GOOGLE", "gemini-2.0-flash-exp")
LLM_MODEL_OPENROUTER: str = os.environ.get(
    "LLM_MODEL_OPENROUTER", "google/gemini-2.0-flash-exp:free"
)

# API
API_PREFIX = "/api"

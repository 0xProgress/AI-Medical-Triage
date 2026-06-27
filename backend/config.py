import os
from pathlib import Path
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models" / "cache"

DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_DB_PATH = DATA_DIR / "symcat.db"
JSON_DB_PATH = DATA_DIR / "symcat_simplified.json"

class Config:
    APP_NAME = "AI Medical Triage"
    APP_VERSION = "0.1.0"
    
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    MODELS_DIR = MODELS_DIR
    SQLITE_DB_PATH = SQLITE_DB_PATH
    JSON_DB_PATH = JSON_DB_PATH
    
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    HF_API_TOKEN = os.getenv("HF_API_TOKEN", None)
    HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    HF_API_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")
    
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))
    MAX_TURNS = int(os.getenv("MAX_TURNS", "10"))
    
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

config = Config()
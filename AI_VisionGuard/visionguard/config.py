import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "AI VisionGuard")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visionguard.db")
    USE_YOLO = os.getenv("USE_YOLO", "true").lower() == "true"
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATES_DIR = BASE_DIR / "templates"
    MEDIA_DIR = BASE_DIR / "media"


settings = Settings()

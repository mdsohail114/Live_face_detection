"""Application configuration loaded from environment variables."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
load_dotenv(BASE_DIR / ".env")


def _bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _secret_key():
    """
    Use SECRET_KEY from .env when provided.
    Otherwise generate a local key file under instance/ so source code never
    contains a hard-coded secret.
    """
    env_key = (os.getenv("SECRET_KEY") or "").strip()
    if env_key and env_key not in {"replace-this-with-a-long-random-string"}:
        return env_key

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    key_path = INSTANCE_DIR / "secret_key.txt"
    if key_path.exists():
        stored = key_path.read_text(encoding="utf-8").strip()
        if stored:
            return stored
    generated = secrets.token_hex(32)
    key_path.write_text(generated, encoding="utf-8")
    return generated


class Config:
    """Central settings. Secrets must come from .env, never from source code."""

    SECRET_KEY = _secret_key()
    DEBUG = _bool_env("FLASK_DEBUG", True)
    INSTANCE_DIR = INSTANCE_DIR
    DATABASE_PATH = Path(
        os.getenv("DATABASE_PATH") or (INSTANCE_DIR / "emergency_safety.db")
    )
    if not DATABASE_PATH.is_absolute():
        DATABASE_PATH = BASE_DIR / DATABASE_PATH

    DATA_DIR = BASE_DIR / "data"
    MODEL_DIR = BASE_DIR / "model"
    DATASET_PATH = DATA_DIR / "emergency_dataset.csv"
    MODEL_PATH = MODEL_DIR / "risk_model.pkl"

    # Twilio
    TWILIO_ACCOUNT_SID = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
    TWILIO_AUTH_TOKEN = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
    TWILIO_FROM_NUMBER = (os.getenv("TWILIO_FROM_NUMBER") or "").strip()

    # Email
    SMTP_HOST = (os.getenv("SMTP_HOST") or "smtp.gmail.com").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
    SMTP_USERNAME = (os.getenv("SMTP_USERNAME") or "").strip()
    SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or "").strip()
    SMTP_FROM_EMAIL = (os.getenv("SMTP_FROM_EMAIL") or "").strip()
    SMTP_USE_TLS = _bool_env("SMTP_USE_TLS", True)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600

    @classmethod
    def sms_configured(cls):
        return bool(
            cls.TWILIO_ACCOUNT_SID
            and cls.TWILIO_AUTH_TOKEN
            and cls.TWILIO_FROM_NUMBER
        )

    @classmethod
    def email_configured(cls):
        return bool(cls.SMTP_USERNAME and cls.SMTP_PASSWORD and cls.SMTP_FROM_EMAIL)

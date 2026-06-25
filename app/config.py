from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/maprk"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_BUCKET: str = "passports"

    UPLOAD_DIR: Path = BASE_DIR / "static" / "uploads"
    PHOTOS_DIR: Path = UPLOAD_DIR / "photos"
    SCHEMES_DIR: Path = UPLOAD_DIR / "schemes"
    PASSPORTS_DIR: Path = UPLOAD_DIR / "passports"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure upload dirs exist
for d in [settings.PHOTOS_DIR, settings.SCHEMES_DIR, settings.PASSPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

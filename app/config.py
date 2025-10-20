from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration values."""

    app_name: str = Field("X-Road Collaboration Portal", description="Human readable name")
    secret_key: str = Field("change-me", description="Secret key for signing JWT tokens")
    access_token_expire_minutes: int = Field(60 * 8, description="Access token lifetime in minutes")
    algorithm: str = Field("HS256", description="JWT signing algorithm")
    database_url: str = Field("sqlite:///./data/app.db", description="Database URL")
    upload_dir: Path = Field(Path("storage/files"), description="Filesystem directory for uploaded files")
    cors_origins: List[AnyHttpUrl] = Field(default_factory=list, description="Allowed CORS origins")
    initial_admin_username: str = Field("admin", description="Username for the bootstrap admin user")
    initial_admin_password: str = Field("admin", description="Password for the bootstrap admin user")
    initial_admin_email: str = Field("admin@example.com", description="Email for the bootstrap admin user")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""

    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings

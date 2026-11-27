"""Application settings loaded from environment variables via pydantic-settings."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration — reads from .env file and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    DATABASE_URL: str = ""
    ALLOWED_ORIGINS: str = (
        "https://fractalvision-frontend.vercel.app,"
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )
    RATE_LIMIT_PER_MINUTE: int = 60
    ANALYSIS_RATE_LIMIT_PER_MINUTE: int = 10
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_IMAGE_DIMENSION: int = 4096
    MAX_IMAGE_PIXELS: int = 16_777_216
    UPLOAD_READ_TIMEOUT_SECONDS: float = 10.0
    ANALYSIS_TIMEOUT_SECONDS: float = 15.0

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, value: str) -> str:
        """Disallow wildcard '*' in CORS origins to prevent overly permissive policies."""
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if "*" in origins:
            raise ValueError("Wildcard '*' is not permitted in ALLOWED_ORIGINS.")
        return ",".join(origins)

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a non-empty list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        """Convert MAX_UPLOAD_SIZE_MB to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

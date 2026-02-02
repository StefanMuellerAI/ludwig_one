"""
Configuration management for LudwigOne API
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    db_host: str = Field(default="postgres", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="ludwigone", alias="DB_NAME")
    db_user: str = Field(default="ludwigone", alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")

    # Temporal
    temporal_host: str = Field(default="temporal:7233", alias="TEMPORAL_HOST")
    temporal_namespace: str = Field(default="default", alias="TEMPORAL_NAMESPACE")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    secret_key: str = Field(alias="SECRET_KEY")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        alias="ALLOWED_ORIGINS"
    )

    # JWT Authentication
    jwt_secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=1440, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours

    # Mistral API
    mistral_api_key: str = Field(alias="MISTRAL_API_KEY")

    # Email
    smtp_host: str = Field(default="smtp.ionos.de", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    recipient_email: Optional[str] = Field(default=None, alias="RECIPIENT_EMAIL")

    # Ollama
    use_ollama: bool = Field(default=False, alias="USE_OLLAMA")
    ollama_url: str = Field(default="http://ollama:11434", alias="OLLAMA_URL")

    # Application
    upload_max_size_mb: int = Field(default=500, alias="UPLOAD_MAX_SIZE_MB")
    output_retention_days: int = Field(default=7, alias="OUTPUT_RETENTION_DAYS")
    max_concurrent_vision_calls: int = Field(default=5, alias="MAX_CONCURRENT_VISION_CALLS")
    vision_api_timeout_seconds: int = Field(default=300, alias="VISION_API_TIMEOUT_SECONDS")
    vision_api_max_retries: int = Field(default=5, alias="VISION_API_MAX_RETRIES")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Get async database URL for SQLAlchemy"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        """Get sync database URL for Alembic"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins as list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use main secret_key if JWT secret not provided
        if not self.jwt_secret_key:
            self.jwt_secret_key = self.secret_key


# Global settings instance
settings = Settings()

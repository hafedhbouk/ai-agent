from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "IA Agent Platform"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production"
    app_api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./data/agent_platform.db"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    chroma_db_path: str = "./data/chroma"

    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"

    rate_limit_default: str = "60/minute"
    rate_limit_chat: str = "20/minute"

    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    agents_dir: str = "./agents"
    prompts_dir: str = "./app/prompts"

    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50

    n8n_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None


settings = Settings()

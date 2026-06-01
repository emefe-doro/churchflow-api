from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ChurchFlow AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DB_TYPE: str = "sqlite"
    DATABASE_URL: str = "sqlite+aiosqlite:///./churchflow.db"
    DATABASE_URL_SYNC: str = "sqlite:///./churchflow.db"

    REDIS_URL: str = "redis://localhost:6379/0"

    WHATSAPP_API_URL: str = "https://graph.facebook.com/v22.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "churchflow-verify-token"
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_MAX_RETRY_ATTEMPTS: int = 3
    WHATSAPP_RETRY_DELAY_SECONDS: int = 300

    AI_PROVIDER: str = "deepseek"
    AI_API_KEY: str = ""
    AI_API_BASE_URL: str = "https://api.deepseek.com"
    AI_MODEL: str = "deepseek-chat"
    AI_MAX_TOKENS: int = 512
    AI_TEMPERATURE: float = 0.7
    AI_TIMEOUT_SECONDS: int = 30
    AI_FALLBACK_TO_TEMPLATE: bool = True

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

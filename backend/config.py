from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "School Management System"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./school.db"

    JWT_SECRET: str = "replace_with_a_strong_random_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    CORS_ORIGINS: str = "*"
    LOG_FILE: str = "logs/app.log"
    API_V1_PREFIX: str = "/api/v1"

    # Email (used for password reset). Optional — if not configured, the
    # forgot-password endpoint still works but logs the reset link to the
    # server console instead of emailing it (fine for local dev/testing;
    # set these for real deployments so users actually receive the email).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "School Hub"

    # Used to build the password reset link sent in the email.
    # e.g. https://schoolhub-ivory.vercel.app
    FRONTEND_BASE_URL: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

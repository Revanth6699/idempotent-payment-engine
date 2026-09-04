import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""

    APP_NAME: str = os.getenv(
        "APP_NAME",
        "Idempotent Payment Processing & Transaction Reconciliation Engine",
    )

    APP_VERSION: str = os.getenv(
        "APP_VERSION",
        "0.1.0",
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://payment_user:payment_password@localhost:5433/payment_engine",
    )

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "15",
        )
    )


settings = Settings()
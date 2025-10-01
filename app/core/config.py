"""
DeepCalm — Configuration Settings

Загружает настройки из .env файла используя pydantic-settings.
Следует стандартам из cortex/STANDARDS.yml (env_prefix: DC_)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Настройки приложения из переменных окружения.

    Все переменные должны начинаться с DC_ согласно STANDARDS.yml
    Примеры: DC_APP_ENV, DC_DATABASE_URL, DC_OPENAI_API_KEY
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # App Settings
    app_env: str = "dev"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "postgresql://dc:dcpass@localhost:5432/deep_calm_dev"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Парсит CORS origins из строки"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # OpenAI / LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # VK Ads (myTarget)
    vk_app_id: str = ""
    vk_app_secret: str = ""
    vk_access_token: str = ""

    # Яндекс.Директ
    yandex_direct_token: str = ""
    yandex_direct_login: str = ""

    # Avito
    avito_client_id: str = ""
    avito_client_secret: str = ""

    # YCLIENTS
    yclients_token: str = ""
    yclients_company_id: int = 0

    # Яндекс.Метрика
    yandex_metrika_token: str = ""
    yandex_metrika_counter_id: int = 0

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Monitoring
    prometheus_port: int = 9090

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Nightly Jobs
    enable_scheduler: bool = True
    sync_spend_cron: str = "0 3 * * *"
    sync_bookings_cron: str = "0 * * * *"
    compute_marts_cron: str = "0 4 * * *"
    upload_conversions_cron: str = "0 5 * * *"
    analyst_report_cron: str = "0 9 * * MON"

    @property
    def is_dev(self) -> bool:
        """Проверка development окружения"""
        return self.app_env == "dev"

    @property
    def is_test(self) -> bool:
        """Проверка test окружения"""
        return self.app_env == "test"

    @property
    def is_prod(self) -> bool:
        """Проверка production окружения"""
        return self.app_env == "prod"


# Singleton instance
settings = Settings()

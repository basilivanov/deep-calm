"""
DeepCalm — Яндекс.Директ Integration (Mock для MVP)

Mock коннектор для Яндекс.Директ API v5.
Реальная интеграция — Phase 1+ (когда будут токены).
"""
import uuid
import structlog
from typing import Dict

logger = structlog.get_logger(__name__)


class YandexDirectClient:
    """
    Mock клиент для Яндекс.Директ API v5.

    Phase 1 (MVP): Mock responses
    Phase 1+: Реальная интеграция через https://api.direct.yandex.com/json/v5/
    """

    def __init__(self, token: str = "", login: str = ""):
        """
        Инициализация клиента.

        Args:
            token: OAuth токен
            login: Яндекс логин
        """
        self.token = token
        self.login = login
        logger.info("yandex_direct_client_initialized", login=login)

    def create_campaign(
        self,
        title: str,
        body: str,
        image_url: str,
        budget_rub: float
    ) -> str:
        """
        Создаёт кампанию в Яндекс.Директ (mock).

        Args:
            title: Название креатива
            body: Текст креатива
            image_url: URL изображения
            budget_rub: Бюджет в рублях

        Returns:
            external_campaign_id (str)
        """
        logger.info(
            "yandex_campaign_create_mock",
            title=title,
            budget_rub=budget_rub
        )

        external_campaign_id = f"direct_camp_{uuid.uuid4().hex[:8]}"

        logger.info(
            "yandex_campaign_created_mock",
            external_campaign_id=external_campaign_id
        )

        return external_campaign_id

    def pause_campaign(self, external_campaign_id: str) -> Dict:
        """Приостановить кампанию (mock)"""
        logger.info("yandex_campaign_pause_mock", campaign_id=external_campaign_id)
        return {"status": "paused"}

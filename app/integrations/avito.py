"""
DeepCalm — Avito Integration (Mock)

Mock коннектор для Avito XML автозагрузки.
Реальная интеграция — Phase 1+ (когда будут токены).
"""
import uuid
import structlog
from typing import Dict

logger = structlog.get_logger(__name__)


class AvitoClient:
    """
    Mock клиент для Avito XML API.

    Phase 1 (MVP): Mock responses
    Phase 1+: Реальная интеграция через https://api.avito.ru/v2/items/upload
    """

    def __init__(self, client_id: str = "", client_secret: str = ""):
        """
        Инициализация клиента.

        Args:
            client_id: Avito Client ID
            client_secret: Avito Client Secret
        """
        self.client_id = client_id
        logger.info("avito_client_initialized", client_id=client_id)

    def create_ad(
        self,
        title: str,
        body: str,
        image_url: str
    ) -> str:
        """
        Создаёт объявление в Avito (mock).

        Args:
            title: Заголовок
            body: Описание
            image_url: URL изображения

        Returns:
            external_ad_id (str)
        """
        logger.info(
            "avito_ad_create_mock",
            title=title
        )

        external_ad_id = f"avito_ad_{uuid.uuid4().hex[:8]}"

        logger.info(
            "avito_ad_created_mock",
            external_ad_id=external_ad_id
        )

        return external_ad_id

    def pause_ad(self, external_ad_id: str) -> Dict:
        """Снять объявление с публикации (mock)"""
        logger.info("avito_ad_pause_mock", ad_id=external_ad_id)
        return {"status": "paused"}

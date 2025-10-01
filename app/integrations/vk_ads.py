"""
DeepCalm — VK Ads Integration (Mock)

Mock коннектор для VK Ads.
Согласно DEEP-CALM-MVP-BLUEPRINT.md: для MVP используем mock,
т.к. официального VK Ads API для создания кампаний нет в открытом доступе.
"""
import uuid
import structlog
from typing import Dict

logger = structlog.get_logger(__name__)


class VKAdsClient:
    """
    Mock клиент для VK Ads.

    Phase 1 (MVP): Возвращает фейковые external_campaign_id
    Phase 2+: Реальная интеграция через myTarget или VK Ads API (если появится)
    """

    def __init__(self, app_id: str = "", app_secret: str = "", access_token: str = ""):
        """
        Инициализация клиента.

        Args:
            app_id: VK App ID
            app_secret: VK App Secret
            access_token: VK Access Token
        """
        self.app_id = app_id
        self.access_token = access_token
        logger.info("vk_ads_client_initialized", app_id=app_id)

    def create_campaign(
        self,
        title: str,
        body: str,
        image_url: str,
        budget_rub: float
    ) -> str:
        """
        Создаёт кампанию в VK Ads (mock).

        Args:
            title: Название креатива
            body: Текст креатива
            image_url: URL изображения
            budget_rub: Бюджет в рублях

        Returns:
            external_campaign_id (str)

        Examples:
            >>> client = VKAdsClient()
            >>> result = client.create_campaign("Test", "Body", "url", 10000)
            >>> result.startswith("vk_camp_")
            True
        """
        logger.info(
            "vk_campaign_create_mock",
            title=title,
            budget_rub=budget_rub
        )

        # Mock response
        external_campaign_id = f"vk_camp_{uuid.uuid4().hex[:8]}"

        logger.info(
            "vk_campaign_created_mock",
            external_campaign_id=external_campaign_id
        )

        return external_campaign_id

    def pause_campaign(self, external_campaign_id: str) -> Dict:
        """Приостановить кампанию (mock)"""
        logger.info("vk_campaign_pause_mock", campaign_id=external_campaign_id)
        return {"status": "paused"}

    def resume_campaign(self, external_campaign_id: str) -> Dict:
        """Возобновить кампанию (mock)"""
        logger.info("vk_campaign_resume_mock", campaign_id=external_campaign_id)
        return {"status": "active"}

"""
Сервис публикации креативов на рекламные платформы
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.avito import AvitoClient
from app.integrations.vk_ads import VKAdsClient
from app.integrations.yandex_direct import YandexDirectClient
from app.models.campaign import Campaign
from app.models.creative import Creative
from app.models.placement import Placement

logger = structlog.get_logger()


class PublishingService:
    """Сервис для публикации креативов на рекламные платформы"""

    def __init__(self, db: Session):
        self.db = db
        self.vk_client = VKAdsClient()
        self.direct_client = YandexDirectClient(
            token=settings.yandex_direct_token or None,
            login=settings.yandex_direct_login or None,
            sandbox=not settings.is_prod,
        )
        self.avito_client = AvitoClient()

    def publish_campaign(
        self,
        campaign_id: UUID,
        channels: Optional[List[str]] = None
    ) -> dict:
        """
        Публикует кампанию на указанные каналы

        Args:
            campaign_id: ID кампании
            channels: Список каналов для публикации. Если None - публикуем во все каналы кампании

        Returns:
            dict с информацией о созданных размещениях
        """
        logger.info("publishing_campaign_started", campaign_id=str(campaign_id), channels=channels)

        # Получаем кампанию
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error("campaign_not_found", campaign_id=str(campaign_id))
            raise ValueError(f"Кампания {campaign_id} не найдена")

        # Определяем каналы для публикации
        target_channels = channels if channels else campaign.channels
        if not target_channels:
            logger.warning("no_channels_specified", campaign_id=str(campaign_id))
            raise ValueError("Не указаны каналы для публикации")

        # Получаем креативы кампании
        creatives = (
            self.db.query(Creative)
            .filter(Creative.campaign_id == campaign_id)
            .filter(Creative.moderation_status == "approved")
            .all()
        )

        if not creatives:
            logger.warning("no_approved_creatives", campaign_id=str(campaign_id))
            raise ValueError(f"Нет одобренных креативов для кампании {campaign_id}")

        placements = []
        success_count = 0
        failed_count = 0

        # Публикуем на каждый канал
        for channel in target_channels:
            for creative in creatives:
                try:
                    placement = self._publish_to_channel(campaign, creative, channel)
                    placements.append(placement)
                    success_count += 1
                    logger.info(
                        "placement_created",
                        campaign_id=str(campaign_id),
                        creative_id=str(creative.id),
                        channel=channel,
                        placement_id=str(placement.id)
                    )
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        "placement_failed",
                        campaign_id=str(campaign_id),
                        creative_id=str(creative.id),
                        channel=channel,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )

        self.db.commit()

        logger.info(
            "publishing_campaign_completed",
            campaign_id=str(campaign_id),
            success_count=success_count,
            failed_count=failed_count
        )

        return {
            "placements": placements,
            "success_count": success_count,
            "failed_count": failed_count
        }

    def _publish_to_channel(
        self,
        campaign: Campaign,
        creative: Creative,
        channel: str
    ) -> Placement:
        """
        Публикует креатив на конкретный канал

        Args:
            campaign: Кампания
            creative: Креатив
            channel: Канал (vk/direct/avito)

        Returns:
            Созданный Placement
        """
        logger.info(
            "publishing_to_channel_started",
            campaign_id=str(campaign.id),
            creative_id=str(creative.id),
            channel=channel,
            creative_title=creative.title,
            budget=campaign.budget_rub
        )

        # Выбираем клиент в зависимости от канала
        if channel == "vk":
            logger.info("using_vk_client")
            external_id = self.vk_client.create_campaign(
                title=creative.title,
                body=creative.body,
                image_url=creative.image_url,
                budget_rub=campaign.budget_rub
            )
        elif channel == "direct":
            logger.info("using_yandex_direct_client", token_exists=bool(self.direct_client.token))
            external_id = self.direct_client.create_campaign(
                title=creative.title,
                body=creative.body,
                image_url=creative.image_url,
                budget_rub=campaign.budget_rub
            )
        elif channel == "avito":
            logger.info("using_avito_client")
            external_id = self.avito_client.create_ad(
                title=creative.title,
                body=creative.body,
                image_url=creative.image_url
            )
        else:
            raise ValueError(f"Неизвестный канал: {channel}")

        logger.info(
            "external_campaign_created",
            channel=channel,
            external_id=external_id
        )

        # Создаем запись о размещении
        placement = Placement(
            campaign_id=campaign.id,
            creative_id=creative.id,
            channel_code=channel,
            external_campaign_id=external_id,
            status="active",
            published_at=datetime.now(timezone.utc)
        )
        self.db.add(placement)

        return placement

    def get_campaign_status(self, campaign_id: UUID) -> dict:
        """
        Получает статус публикации кампании

        Args:
            campaign_id: ID кампании

        Returns:
            dict со статистикой размещений
        """
        logger.info("getting_campaign_status", campaign_id=str(campaign_id))

        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error("campaign_not_found", campaign_id=str(campaign_id))
            raise ValueError(f"Кампания {campaign_id} не найдена")

        placements = (
            self.db.query(Placement)
            .filter(Placement.campaign_id == campaign_id)
            .all()
        )

        active_count = sum(1 for p in placements if p.status == "active")
        paused_count = sum(1 for p in placements if p.status == "paused")
        failed_count = sum(1 for p in placements if p.status == "failed")

        return {
            "campaign": campaign,
            "total_placements": len(placements),
            "active_placements": active_count,
            "paused_placements": paused_count,
            "failed_placements": failed_count,
            "placements": placements
        }

    def pause_campaign(self, campaign_id: UUID) -> dict:
        """
        Приостанавливает все размещения кампании

        Args:
            campaign_id: ID кампании

        Returns:
            dict с количеством приостановленных размещений
        """
        logger.info("pausing_campaign", campaign_id=str(campaign_id))

        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error("campaign_not_found", campaign_id=str(campaign_id))
            raise ValueError(f"Кампания {campaign_id} не найдена")

        placements = (
            self.db.query(Placement)
            .filter(Placement.campaign_id == campaign_id)
            .filter(Placement.status == "active")
            .all()
        )

        paused_count = 0
        failed_count = 0

        for placement in placements:
            try:
                # Приостанавливаем на платформе
                if placement.channel_code == "vk":
                    self.vk_client.pause_campaign(placement.external_campaign_id)
                elif placement.channel_code == "direct":
                    self.direct_client.pause_campaign(placement.external_campaign_id)
                elif placement.channel_code == "avito":
                    self.avito_client.pause_ad(placement.external_campaign_id)

                # Обновляем статус
                placement.status = "paused"
                paused_count += 1

                logger.info(
                    "placement_paused",
                    placement_id=str(placement.id),
                    channel=placement.channel_code,
                    external_id=placement.external_campaign_id
                )
            except Exception as e:
                failed_count += 1
                logger.error(
                    "placement_pause_failed",
                    placement_id=str(placement.id),
                    channel=placement.channel,
                    error=str(e)
                )

        self.db.commit()

        logger.info(
            "campaign_paused",
            campaign_id=str(campaign_id),
            paused_count=paused_count,
            failed_count=failed_count
        )

        return {
            "paused_count": paused_count,
            "failed_count": failed_count
        }

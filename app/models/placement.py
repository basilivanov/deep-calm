"""
DeepCalm — Placement Model

Модель размещения креатива на площадке.
Схема из cortex/DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Placement(Base):
    """
    Размещение креатива на рекламной площадке.

    Attributes:
        id: UUID размещения
        campaign_id: ID кампании
        creative_id: ID креатива
        channel_code: Код площадки (vk, direct, avito)
        external_campaign_id: ID кампании от площадки
        external_ad_id: ID объявления от площадки
        status: Статус (pending|published|active|paused|failed)
        error_message: Сообщение об ошибке (если failed)
        published_at: Дата публикации
        created_at: Дата создания

    Examples:
        >>> placement = Placement(
        ...     campaign_id=campaign.id,
        ...     creative_id=creative.id,
        ...     channel_code="vk",
        ...     status="published"
        ... )
    """
    __tablename__ = "placements"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    creative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("creatives.id", ondelete="SET NULL"),
        index=True
    )
    channel_code = Column(String(20), nullable=False, index=True)
    external_campaign_id = Column(Text)
    external_ad_id = Column(Text)
    status = Column(
        String(20),
        default="pending"
    )  # pending|published|active|paused|failed
    error_message = Column(Text)

    published_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="placements")
    creative = relationship("Creative", back_populates="placements")

    def __repr__(self) -> str:
        return f"<Placement id={self.id} channel={self.channel_code} status={self.status}>"

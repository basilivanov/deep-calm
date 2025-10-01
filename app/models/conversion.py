"""
DeepCalm — Conversion Model

Модель конверсии (booking confirmed + paid).
Схема из cortex/DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class Conversion(Base):
    """
    Конверсия = booking confirmed + payment captured.

    Attributes:
        id: ID конверсии (serial)
        lead_id: ID лида
        booking_id: ID записи (из YCLIENTS)
        campaign_id: ID кампании (nullable для organic)
        channel_code: Код площадки (vk, direct, avito)
        ttp_days: Time To Purchase (дни от клика до оплаты)
        revenue_rub: Выручка в рублях
        converted_at: Дата конверсии
        created_at: Дата создания записи

    Examples:
        >>> conversion = Conversion(
        ...     lead_id=lead.id,
        ...     campaign_id=campaign.id,
        ...     channel_code="vk",
        ...     ttp_days=2,
        ...     revenue_rub=3500,
        ...     converted_at=datetime.now()
        ... )
    """
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    booking_id = Column(Integer, index=True)  # из YCLIENTS
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        index=True
    )
    channel_code = Column(String(20), index=True)
    ttp_days = Column(Integer)  # Time To Purchase
    revenue_rub = Column(Numeric(10, 2), nullable=False)

    converted_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="conversions")

    def __repr__(self) -> str:
        return f"<Conversion id={self.id} lead_id={self.lead_id} revenue={self.revenue_rub}₽>"

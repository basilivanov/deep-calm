"""
DeepCalm — Campaign Model

Модель рекламной кампании.
Схема из cortex/DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Boolean, ARRAY, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Campaign(Base):
    """
    Рекламная кампания.

    Attributes:
        id: UUID кампании
        title: Название кампании
        sku: SKU услуги (RELAX-60, DEEP-90, etc.)
        budget_rub: Бюджет в рублях
        target_cac_rub: Целевой CAC (Customer Acquisition Cost)
        target_roas: Целевой ROAS (Return on Ad Spend)
        channels: Площадки ['vk', 'direct', 'avito']
        status: Статус (draft|active|paused|stopped)
        ab_test_enabled: Включен ли A/B тест креативов
        created_at: Дата создания
        updated_at: Дата последнего обновления

    Examples:
        >>> campaign = Campaign(
        ...     title="Запуск сентябрь — Релакс",
        ...     sku="RELAX-60",
        ...     budget_rub=15000,
        ...     channels=["vk", "direct"]
        ... )
        >>> db.add(campaign)
        >>> db.commit()
    """
    __tablename__ = "campaigns"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title = Column(String(255), nullable=False)
    sku = Column(String(50), nullable=False)
    budget_rub = Column(Numeric(10, 2), nullable=False)
    target_cac_rub = Column(Numeric(10, 2), default=500)
    target_roas = Column(Numeric(5, 2), default=5.0)
    channels = Column(ARRAY(String), nullable=False)
    status = Column(
        String(20),
        default="draft",
        nullable=False
    )  # draft|active|paused|stopped
    ab_test_enabled = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    creatives = relationship("Creative", back_populates="campaign", cascade="all, delete-orphan")
    placements = relationship("Placement", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} title='{self.title}' status={self.status}>"

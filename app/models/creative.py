"""
DeepCalm — Creative Model

Модель креатива для A/B тестирования.
Схема из cortex/DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Creative(Base):
    """
    Креатив для рекламной кампании (A/B/C варианты).

    Attributes:
        id: UUID креатива
        campaign_id: ID кампании
        variant: Вариант (A, B, C)
        title: Заголовок креатива
        body: Текст объявления
        image_url: URL изображения
        cta: Call-to-Action текст ("Записаться", "Узнать больше")
        generated_by: Источник (llm|manual)
        moderation_status: Статус модерации (pending|approved|rejected)
        created_at: Дата создания

    Examples:
        >>> creative = Creative(
        ...     campaign_id=campaign.id,
        ...     variant="A",
        ...     title="Релакс массаж 60 минут",
        ...     body="Глубокое расслабление. Без боли. Тишина на час.",
        ...     cta="Записаться"
        ... )
    """
    __tablename__ = "creatives"

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
    variant = Column(String(10), nullable=False)  # A, B, C
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    image_url = Column(Text)
    cta = Column(Text)  # Call-to-Action
    generated_by = Column(String(50), default="llm")  # llm|manual
    moderation_status = Column(
        String(20),
        default="pending"
    )  # pending|approved|rejected

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="creatives")
    placements = relationship("Placement", back_populates="creative")

    def __repr__(self) -> str:
        return f"<Creative id={self.id} campaign_id={self.campaign_id} variant={self.variant}>"

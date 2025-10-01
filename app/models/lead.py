"""
DeepCalm — Lead Model

Модель лида (Identity Map).
Схема из cortex/DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Lead(Base):
    """
    Лид (клиент с UTM-метками для атрибуции).

    Identity Map: ключ - телефон.

    Attributes:
        id: UUID лида
        phone: Телефон +79991234567 (уникальный)
        utm_source: Источник (vk, direct, avito)
        utm_campaign: Название кампании
        utm_content: ID креатива (для A/B тестов)
        utm_medium: Модель оплаты (cpc, cpm)
        utm_term: Ключевая фраза (Директ)
        web_id: localStorage UUID (fallback)
        client_id: Метрика ClientId
        yclients_id: ID из YCLIENTS
        first_touch_at: Время первого клика
        created_at: Дата создания

    Examples:
        >>> lead = Lead(
        ...     phone="+79991234567",
        ...     utm_source="vk",
        ...     utm_campaign="zapusk-sentyabr",
        ...     web_id="550e8400-e29b-41d4-a716-446655440000"
        ... )
    """
    __tablename__ = "leads"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    phone = Column(String(20), unique=True, nullable=False, index=True)

    # UTM метки
    utm_source = Column(String(50), index=True)  # vk, direct, avito
    utm_campaign = Column(String(100))
    utm_content = Column(String(100))  # creative_id
    utm_medium = Column(String(50))  # cpc, cpm
    utm_term = Column(String(100))  # ключевая фраза

    # Web tracking
    web_id = Column(Text)  # localStorage UUID
    client_id = Column(Text)  # Метрика ClientId

    # YCLIENTS integration
    yclients_id = Column(Integer)

    # Timestamps
    first_touch_at = Column(TIMESTAMP(timezone=True), index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    conversions = relationship("Conversion", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Lead id={self.id} phone={self.phone} source={self.utm_source}>"

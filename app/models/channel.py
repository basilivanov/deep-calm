"""
DeepCalm — Channel Model

Справочник рекламных площадок.
Схема из cortex/DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, TIMESTAMP

from app.core.db import Base


class Channel(Base):
    """
    Справочник рекламных площадок.

    Attributes:
        id: ID площадки (serial)
        code: Код площадки (vk, direct, avito) - уникальный
        name: Название площадки
        api_endpoint: URL API endpoint
        enabled: Включена ли площадка
        created_at: Дата создания

    Examples:
        >>> vk = Channel(code="vk", name="VK Ads", enabled=True)
        >>> direct = Channel(code="direct", name="Яндекс.Директ", enabled=True)
        >>> avito = Channel(code="avito", name="Avito", enabled=True)
    """
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    api_endpoint = Column(Text)
    enabled = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Channel code={self.code} name='{self.name}' enabled={self.enabled}>"

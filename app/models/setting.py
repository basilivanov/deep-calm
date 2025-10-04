"""
DeepCalm — SQLAlchemy Model for Settings
"""
from sqlalchemy import Column, String, Text, DateTime, func
from app.core.db import Base

class Setting(Base):
    """
    Модель для хранения настроек системы в формате key-value.
    
    Схема соответствует cortex/DEEP-CALM-MVP-BLUEPRINT.md
    """
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True, comment="Ключ настройки")
    value = Column(Text, nullable=False, comment="Значение настройки")
    value_type = Column(String(20), nullable=False, comment="Тип значения: int, float, string, bool")
    category = Column(String(50), nullable=False, index=True, comment="Категория: financial, pricing, alerts, ai, operational")
    description = Column(Text, nullable=True, comment="Описание настройки")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Время последнего обновления")
    updated_by = Column(String(50), nullable=True, default="system", comment="Кто обновил")

    def __repr__(self):
        return f"<Setting(key='{self.key}', value='{self.value}')>"

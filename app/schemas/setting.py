"""
DeepCalm — Settings Schemas

Pydantic схемы для Settings API.
Поддерживает типизированные настройки для AI Analyst.
"""
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SettingBase(BaseModel):
    """Базовая схема для настройки"""
    key: str = Field(..., max_length=100, description="Ключ настройки")
    value: str = Field(..., description="Значение настройки")
    value_type: str = Field(..., max_length=20, description="Тип значения: int, float, string, bool")
    category: str = Field(..., max_length=50, description="Категория: financial, pricing, alerts, ai, operational")
    description: Optional[str] = Field(None, description="Описание настройки")
    updated_by: Optional[str] = Field("system", max_length=50, description="Кто обновил")

    @field_validator('value_type')
    @classmethod
    def validate_value_type(cls, v):
        allowed_types = ['int', 'float', 'string', 'bool']
        if v not in allowed_types:
            raise ValueError(f'value_type должен быть одним из: {allowed_types}')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        allowed_categories = ['financial', 'pricing', 'alerts', 'ai', 'operational']
        if v not in allowed_categories:
            raise ValueError(f'category должна быть одной из: {allowed_categories}')
        return v


class SettingCreate(SettingBase):
    """Схема для создания настройки"""
    pass


class SettingUpdate(BaseModel):
    """Схема для обновления настройки"""
    value: Optional[str] = Field(None, description="Новое значение настройки")
    description: Optional[str] = Field(None, description="Новое описание")
    updated_by: Optional[str] = Field(None, max_length=50, description="Кто обновил")


class SettingResponse(SettingBase):
    """Схема ответа для настройки"""
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")

    class Config:
        from_attributes = True


class SettingListResponse(BaseModel):
    """Схема ответа для списка настроек"""
    settings: List[SettingResponse]
    total: int = Field(..., description="Общее количество настроек")
    page: int = Field(..., description="Номер страницы")
    page_size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")


class SettingValueResponse(BaseModel):
    """Схема для получения типизированного значения настройки"""
    key: str = Field(..., description="Ключ настройки")
    value: Union[bool, int, float, str] = Field(..., description="Типизированное значение")
    value_type: str = Field(..., description="Тип значения")
    category: str = Field(..., description="Категория настройки")


class BulkSettingsUpdate(BaseModel):
    """Схема для массового обновления настроек"""
    settings: List[SettingCreate] = Field(..., description="Список настроек для обновления")
    updated_by: str = Field("system", description="Кто обновил")


class SettingsByCategory(BaseModel):
    """Схема для получения настроек по категории"""
    category: str = Field(..., description="Категория")
    settings: List[SettingResponse] = Field(..., description="Настройки категории")
    count: int = Field(..., description="Количество настроек в категории")

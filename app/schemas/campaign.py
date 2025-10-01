"""
DeepCalm — Campaign Schemas

Pydantic schemas для валидации Campaign API.
Следует DEEP-CALM-MVP-BLUEPRINT.md
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class CampaignBase(BaseModel):
    """Базовые поля кампании"""
    title: str = Field(..., min_length=3, max_length=255, description="Название кампании")
    sku: str = Field(..., pattern="^[A-Z]+-[0-9]+$", description="SKU услуги (RELAX-60, DEEP-90)")
    budget_rub: float = Field(..., gt=0, description="Бюджет в рублях")
    target_cac_rub: float = Field(default=500, ge=0, description="Целевой CAC")
    target_roas: float = Field(default=5.0, ge=0, description="Целевой ROAS")
    channels: List[str] = Field(..., min_length=1, description="Площадки: vk, direct, avito")
    ab_test_enabled: bool = Field(default=False, description="Включен ли A/B тест")

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v: List[str]) -> List[str]:
        """
        Валидация площадок.

        Разрешены только: vk, direct, avito
        Согласно STANDARDS.yml
        """
        allowed = {"vk", "direct", "avito"}
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"Недопустимые каналы: {invalid}. Разрешены: {allowed}")
        return v

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """
        Валидация SKU.

        Исключаем TANTRA-120, YONI-240 согласно STANDARDS.yml (publishing.exclude_sku)
        """
        excluded = ["TANTRA-120", "YONI-240"]
        if v in excluded:
            raise ValueError(f"SKU '{v}' запрещён для публикации (модерация)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Запуск сентябрь — Релакс",
                "sku": "RELAX-60",
                "budget_rub": 15000,
                "target_cac_rub": 450,
                "target_roas": 5.0,
                "channels": ["vk", "direct"],
                "ab_test_enabled": True
            }
        }


class CampaignCreate(CampaignBase):
    """Схема создания кампании"""
    pass


class CampaignUpdate(BaseModel):
    """Схема обновления кампании (все поля опциональные)"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    budget_rub: Optional[float] = Field(None, gt=0)
    target_cac_rub: Optional[float] = Field(None, ge=0)
    target_roas: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|stopped)$")
    ab_test_enabled: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "budget_rub": 20000
            }
        }


class CampaignResponse(CampaignBase):
    """Схема ответа API (Campaign из БД)"""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (было orm_mode)


class CampaignListResponse(BaseModel):
    """Список кампаний с пагинацией"""
    items: List[CampaignResponse]
    total: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20
            }
        }

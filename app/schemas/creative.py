"""
DeepCalm — Creative Schemas

Pydantic schemas для валидации Creative API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class CreativeBase(BaseModel):
    """Базовые поля креатива"""
    variant: str = Field(..., pattern="^[A-C]$", description="Вариант креатива (A, B, C)")
    title: str = Field(..., min_length=1, max_length=500, description="Заголовок")
    body: str = Field(..., min_length=1, max_length=2000, description="Текст объявления")
    image_url: Optional[str] = Field(None, description="URL изображения")
    cta: Optional[str] = Field(None, max_length=100, description="Call-to-Action")

    class Config:
        json_schema_extra = {
            "example": {
                "variant": "A",
                "title": "Релакс массаж 60 минут",
                "body": "Глубокое расслабление. Без боли. Тишина на час.",
                "cta": "Записаться"
            }
        }


class CreativeCreate(CreativeBase):
    """Схема создания креатива"""
    campaign_id: UUID = Field(..., description="ID кампании")
    generated_by: str = Field(default="manual", pattern="^(llm|manual)$")


class CreativeGenerateRequest(BaseModel):
    """Запрос на генерацию креативов через LLM"""
    campaign_id: UUID = Field(..., description="ID кампании")
    count: int = Field(default=3, ge=1, le=5, description="Количество вариантов (1-5)")
    temperature: float = Field(default=0.8, ge=0.0, le=2.0, description="Креативность LLM")

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "550e8400-e29b-41d4-a716-446655440001",
                "count": 3,
                "temperature": 0.8
            }
        }


class CreativeResponse(CreativeBase):
    """Схема ответа API"""
    id: UUID
    campaign_id: UUID
    generated_by: str
    moderation_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreativeListResponse(BaseModel):
    """Список креативов"""
    items: list[CreativeResponse]
    total: int

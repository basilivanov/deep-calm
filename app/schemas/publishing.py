"""
Pydantic schemas для Publishing API
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    """Запрос на публикацию кампании"""
    campaign_id: UUID = Field(..., description="ID кампании для публикации")
    channels: Optional[List[str]] = Field(
        None,
        description="Список каналов для публикации. Если None - публикуем во все каналы кампании"
    )


class PlacementInfo(BaseModel):
    """Информация о размещении"""
    placement_id: UUID
    channel: str
    creative_variant: str
    external_id: str
    status: str
    created_at: datetime


class PublishResponse(BaseModel):
    """Ответ после публикации"""
    campaign_id: UUID
    placements: List[PlacementInfo]
    success_count: int
    failed_count: int
    message: str


class PublishingStatusResponse(BaseModel):
    """Статус публикации кампании"""
    campaign_id: UUID
    campaign_title: str
    total_placements: int
    active_placements: int
    paused_placements: int
    failed_placements: int
    placements: List[PlacementInfo]


class PauseResponse(BaseModel):
    """Ответ после приостановки кампании"""
    campaign_id: UUID
    paused_count: int
    failed_count: int
    message: str

"""
Pydantic schemas для Analytics API
"""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignMetrics(BaseModel):
    """Метрики кампании"""
    campaign_id: UUID
    campaign_title: str
    sku: str

    # Бюджет
    budget_rub: float
    spent_rub: float = Field(0.0, description="Потрачено (из placements)")

    # Целевые метрики
    target_cac_rub: Optional[float]
    target_roas: Optional[float]

    # Фактические метрики
    impressions: int = Field(0, description="Показы")
    clicks: int = Field(0, description="Клики")
    ctr: float = Field(0.0, description="CTR (%)")

    leads_count: int = Field(0, description="Количество лидов")
    conversions_count: int = Field(0, description="Количество конверсий")
    conversion_rate: float = Field(0.0, description="CR (%)")

    revenue_rub: float = Field(0.0, description="Выручка")

    # KPI
    actual_cac_rub: Optional[float] = Field(None, description="Фактический CAC")
    actual_roas: Optional[float] = Field(None, description="Фактический ROAS")

    # Статус целей
    cac_status: str = Field("unknown", description="on_track | over_target | under_target | unknown")
    roas_status: str = Field("unknown", description="on_track | over_target | under_target | unknown")


class ChannelBreakdown(BaseModel):
    """Разбивка метрик по каналу"""
    channel_code: str
    channel_name: str

    placements_count: int
    active_placements: int

    spent_rub: float
    leads_count: int
    conversions_count: int
    revenue_rub: float

    cac_rub: Optional[float]
    roas: Optional[float]


class CampaignAnalyticsResponse(BaseModel):
    """Полная аналитика по кампании"""
    metrics: CampaignMetrics
    channels: list[ChannelBreakdown]


class DashboardSummary(BaseModel):
    """Сводка для дашборда"""
    total_campaigns: int
    active_campaigns: int
    paused_campaigns: int

    total_budget_rub: float
    total_spent_rub: float
    budget_utilization: float = Field(description="Процент использования бюджета")

    total_leads: int
    total_conversions: int
    total_revenue_rub: float

    avg_cac_rub: Optional[float]
    avg_roas: Optional[float]

    top_performing_campaign: Optional[dict] = Field(
        None,
        description="Лучшая кампания по ROAS"
    )


class DateRangeRequest(BaseModel):
    """Запрос с диапазоном дат"""
    start_date: Optional[date] = Field(None, description="Начальная дата (включительно)")
    end_date: Optional[date] = Field(None, description="Конечная дата (включительно)")

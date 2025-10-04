"""
DeepCalm — Reports Schemas

Pydantic схемы для Reports API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReportPeriod(BaseModel):
    """Период отчета"""
    start_date: str = Field(..., description="Дата начала (ISO формат)")
    end_date: str = Field(..., description="Дата окончания (ISO формат)")
    weeks: int = Field(..., description="Количество недель")


class ReportSummary(BaseModel):
    """Сводка метрик"""
    total_leads: int = Field(..., description="Общее количество лидов")
    total_conversions: int = Field(..., description="Общее количество конверсий")
    total_revenue: float = Field(..., description="Общая выручка (рублей)")
    conversion_rate: float = Field(..., description="Общий процент конверсии")
    active_campaigns: int = Field(..., description="Количество активных кампаний")


class CampaignMetric(BaseModel):
    """Метрики кампании"""
    id: int = Field(..., description="ID кампании")
    title: str = Field(..., description="Название кампании")
    sku: str = Field(..., description="SKU продукта")
    status: str = Field(..., description="Статус кампании")
    leads: int = Field(..., description="Количество лидов")
    conversions: int = Field(..., description="Количество конверсий")
    revenue: float = Field(..., description="Выручка (рублей)")
    spend: float = Field(..., description="Расход (рублей)")
    roas: float = Field(..., description="Return on Ad Spend")
    cac: float = Field(..., description="Customer Acquisition Cost")
    target_cac: Optional[float] = Field(None, description="Целевой CAC")
    target_roas: Optional[float] = Field(None, description="Целевой ROAS")


class DetailedReportData(BaseModel):
    """Детальные данные отчета"""
    top_performers: List[CampaignMetric] = Field(..., description="Топ-кампании")
    needs_attention: List[CampaignMetric] = Field(..., description="Кампании, требующие внимания")
    all_campaigns: List[CampaignMetric] = Field(..., description="Все кампании")


class ReportSettings(BaseModel):
    """Настройки отчета"""
    reports_email: str = Field(..., description="Email для отправки отчетов")
    auto_generated: bool = Field(..., description="Автоматически сгенерирован")


class WeeklyReportResponse(BaseModel):
    """Схема ответа еженедельного отчета"""
    id: str = Field(..., description="ID отчета")
    generated_at: str = Field(..., description="Время генерации (ISO формат)")
    period: ReportPeriod = Field(..., description="Период отчета")
    summary: ReportSummary = Field(..., description="Сводка метрик")
    ai_analysis: str = Field(..., description="AI анализ отчета")
    detailed_data: DetailedReportData = Field(..., description="Детальные данные")
    settings: ReportSettings = Field(..., description="Настройки отчета")


class ReportGenerationRequest(BaseModel):
    """Схема запроса генерации отчета"""
    weeks_back: int = Field(1, ge=1, le=12, description="Количество недель назад (1-12)")


class ReportStatusResponse(BaseModel):
    """Схема статуса системы отчетов"""
    reports_enabled: bool = Field(..., description="Включены ли отчеты")
    reports_email: str = Field(..., description="Email для отчетов")
    ai_available: bool = Field(..., description="Доступен ли AI сервис")
    last_check: str = Field(..., description="Время последней проверки")
    message: Optional[str] = Field(None, description="Сообщение о статусе")


class EmailReportResponse(BaseModel):
    """Схема ответа отправки отчета по email"""
    status: str = Field(..., description="Статус отправки")
    message: str = Field(..., description="Сообщение")
    weeks_back: int = Field(..., description="Период отчета")


class WeeklyDataPreview(BaseModel):
    """Схема превью данных недели"""
    period: ReportPeriod = Field(..., description="Период")
    summary: ReportSummary = Field(..., description="Сводка")
    campaigns: List[CampaignMetric] = Field(..., description="Метрики кампаний")
    top_performers: List[CampaignMetric] = Field(..., description="Топ-кампании")
    needs_attention: List[CampaignMetric] = Field(..., description="Проблемные кампании")
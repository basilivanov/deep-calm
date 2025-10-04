"""
DeepCalm — AI Analyst Schemas

Pydantic схемы для AI Analyst API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Схема запроса анализа кампании"""
    question: Optional[str] = Field(None, description="Дополнительный вопрос для анализа")


class CampaignMetrics(BaseModel):
    """Метрики кампании"""
    total_leads: int = Field(..., description="Общее количество лидов")
    total_conversions: int = Field(..., description="Общее количество конверсий")
    conversion_rate: float = Field(..., description="Процент конверсии")
    total_revenue: float = Field(..., description="Общая выручка (рублей)")
    total_spend: float = Field(..., description="Общие расходы (рублей)")
    roas: float = Field(..., description="Return on Ad Spend")
    cac: float = Field(..., description="Customer Acquisition Cost (рублей)")
    period_days: int = Field(..., description="Период анализа (дней)")


class TokenUsage(BaseModel):
    """Использование токенов OpenAI"""
    prompt_tokens: int = Field(..., description="Токены в промпте")
    completion_tokens: int = Field(..., description="Токены в ответе")
    total_tokens: int = Field(..., description="Общее количество токенов")


class CampaignAnalysisResponse(BaseModel):
    """Схема ответа анализа кампании"""
    campaign_id: int = Field(..., description="ID кампании")
    analysis: str = Field(..., description="Текст анализа от AI")
    metrics: CampaignMetrics = Field(..., description="Метрики кампании")
    recommendations: List[str] = Field(..., description="Извлеченные рекомендации")
    generated_at: str = Field(..., description="Время генерации анализа")
    token_usage: TokenUsage = Field(..., description="Использование токенов")


class ChatRequest(BaseModel):
    """Схема запроса чата с аналитиком"""
    message: str = Field(..., max_length=1000, description="Сообщение аналитику")
    campaign_id: Optional[int] = Field(None, description="ID кампании для контекста")


class ChatResponse(BaseModel):
    """Схема ответа чата"""
    response: str = Field(..., description="Ответ аналитика")
    campaign_id: Optional[int] = Field(None, description="ID кампании из контекста")


class AnalysisHistoryItem(BaseModel):
    """Элемент истории анализов"""
    id: int = Field(..., description="ID анализа")
    campaign_id: int = Field(..., description="ID кампании")
    campaign_title: str = Field(..., description="Название кампании")
    summary: str = Field(..., description="Краткое резюме анализа")
    created_at: datetime = Field(..., description="Время создания")
    roas: float = Field(..., description="ROAS на момент анализа")
    cac: float = Field(..., description="CAC на момент анализа")


class AnalysisHistoryResponse(BaseModel):
    """Схема ответа истории анализов"""
    analyses: List[AnalysisHistoryItem] = Field(..., description="История анализов")
    total: int = Field(..., description="Общее количество анализов")
    page: int = Field(..., description="Номер страницы")
    page_size: int = Field(..., description="Размер страницы")


class AnalystHealthResponse(BaseModel):
    """Схема здоровья аналитика"""
    status: str = Field(..., description="Статус сервиса")
    ai_service: Optional[str] = Field(None, description="Статус OpenAI")
    message: Optional[str] = Field(None, description="Сообщение о статусе")
    settings: Optional[Dict[str, Any]] = Field(None, description="Настройки AI")
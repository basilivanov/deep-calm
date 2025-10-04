"""
DeepCalm — AI Analyst API

Endpoints для AI анализа кампаний и чата с аналитиком.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import structlog

from app.core.db import get_db
from app.services.ai_analyst import AIAnalystService
from app.schemas.analyst import (
    CampaignAnalysisResponse,
    AnalysisRequest,
    ChatRequest,
    ChatResponse,
    AnalysisHistoryResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_ai_analyst_service(db: Session = Depends(get_db)) -> AIAnalystService:
    """Dependency для AI Analyst Service"""
    return AIAnalystService(db)


@router.post("/analyst/analyze/{campaign_id}", response_model=CampaignAnalysisResponse)
def analyze_campaign(
    campaign_id: int,
    request: Optional[AnalysisRequest] = None,
    analyst: AIAnalystService = Depends(get_ai_analyst_service)
):
    """
    Анализ кампании через AI Analyst

    Генерирует детальный анализ эффективности кампании с рекомендациями.
    """
    logger.info("analyze_campaign_request", campaign_id=campaign_id)

    try:
        user_question = request.question if request else None
        analysis = analyst.analyze_campaign(campaign_id, user_question)

        return CampaignAnalysisResponse(**analysis)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("analysis_failed", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка анализа кампании")


@router.post("/analyst/chat", response_model=ChatResponse)
def chat_with_analyst(
    request: ChatRequest,
    analyst: AIAnalystService = Depends(get_ai_analyst_service)
):
    """
    Чат с AI аналитиком

    Задавайте вопросы о performance маркетинге и получайте экспертные ответы.
    """
    logger.info("chat_request", message_length=len(request.message))

    try:
        response = analyst.chat_with_analyst(
            message=request.message,
            campaign_id=request.campaign_id
        )

        return ChatResponse(
            response=response,
            campaign_id=request.campaign_id
        )

    except Exception as e:
        logger.error("chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка чата с аналитиком")


@router.get("/analyst/campaign/{campaign_id}/data")
def get_campaign_data_for_analysis(
    campaign_id: int,
    analyst: AIAnalystService = Depends(get_ai_analyst_service)
):
    """
    Получить данные кампании для анализа

    Возвращает структурированные данные кампании с метриками.
    """
    logger.info("get_campaign_data", campaign_id=campaign_id)

    try:
        data = analyst.get_campaign_data(campaign_id)
        return data

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("get_campaign_data_failed", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка получения данных кампании")


@router.get("/analyst/health")
def check_analyst_health(
    analyst: AIAnalystService = Depends(get_ai_analyst_service)
):
    """
    Проверка работоспособности AI Analyst

    Проверяет настройки OpenAI и доступность сервиса.
    """
    try:
        # Проверяем настройки
        if not analyst._settings.get("openai_api_key"):
            return {
                "status": "error",
                "message": "OpenAI API ключ не настроен"
            }

        if analyst._settings.get("openai_api_key") == "sk-your-openai-key-here":
            return {
                "status": "warning",
                "message": "Используется тестовый API ключ"
            }

        # Простой тест OpenAI клиента
        try:
            analyst.openai_client.models.list()
            ai_status = "ok"
        except Exception as e:
            logger.warning("openai_test_failed", error=str(e))
            ai_status = "error"

        return {
            "status": "ok",
            "ai_service": ai_status,
            "settings": {
                "model": analyst._settings.get("ai_model", "gpt-4"),
                "temperature": analyst._settings.get("ai_temperature", 0.3),
                "max_tokens": analyst._settings.get("ai_max_tokens", 2000)
            }
        }

    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {
            "status": "error",
            "message": str(e)
        }
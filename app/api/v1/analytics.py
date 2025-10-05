"""
API endpoints для аналитики кампаний
"""
from datetime import date
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.analytics import (
    CampaignAnalyticsResponse,
    DashboardSummary,
    DateRangeRequest,
    DashboardDailyPoint,
    ChannelPerformanceItem,
)
from app.services.analytics_service import AnalyticsService

logger = structlog.get_logger()
router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    from datetime import datetime

    return datetime.strptime(value, "%Y-%m-%d").date()


@router.get("/campaigns/{campaign_id}", response_model=CampaignAnalyticsResponse)
def get_campaign_analytics(
    campaign_id: UUID,
    start_date: str = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Получает аналитику по кампании

    - **campaign_id**: ID кампании
    - **start_date**: Начальная дата фильтра (опционально)
    - **end_date**: Конечная дата фильтра (опционально)

    Возвращает:
    - Метрики кампании (CAC, ROAS, конверсии, выручка)
    - Разбивку по каналам
    """
    logger.info(
        "get_campaign_analytics_request",
        campaign_id=str(campaign_id),
        start_date=start_date,
        end_date=end_date
    )

    service = AnalyticsService(db)

    try:
        # Парсим даты если есть
        start_date_obj = _parse_date(start_date)
        end_date_obj = _parse_date(end_date)

        result = service.get_campaign_metrics(
            campaign_id=campaign_id,
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        response = CampaignAnalyticsResponse(
            metrics=result["metrics"],
            channels=result["channels"]
        )

        logger.info(
            "get_campaign_analytics_success",
            campaign_id=str(campaign_id),
            leads=result["metrics"].leads_count,
            conversions=result["metrics"].conversions_count
        )

        return response

    except ValueError as e:
        logger.error(
            "get_campaign_analytics_validation_error",
            campaign_id=str(campaign_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "get_campaign_analytics_error",
            campaign_id=str(campaign_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при расчете аналитики"
        )


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    start_date: str = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Получает сводку для дашборда

    - **start_date**: Начальная дата фильтра (опционально)
    - **end_date**: Конечная дата фильтра (опционально)

    Возвращает:
    - Общее количество кампаний (всего, активных, на паузе)
    - Общий бюджет и расход
    - Суммарные лиды, конверсии, выручка
    - Средние CAC и ROAS
    - Лучшая кампания по ROAS
    """
    logger.info(
        "get_dashboard_summary_request",
        start_date=start_date,
        end_date=end_date
    )

    service = AnalyticsService(db)

    try:
        # Парсим даты если есть
        start_date_obj = _parse_date(start_date)
        end_date_obj = _parse_date(end_date)

        summary = service.get_dashboard_summary(
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        logger.info(
            "get_dashboard_summary_success",
            total_campaigns=summary.total_campaigns,
            total_leads=summary.total_leads,
            total_conversions=summary.total_conversions
        )

        return summary

    except Exception as e:
        logger.error(
            "get_dashboard_summary_error",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при расчете сводки"
        )


@router.get("/dashboard/daily", response_model=list[DashboardDailyPoint])
def get_dashboard_daily_metrics(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    service = AnalyticsService(db)
    try:
        return service.get_dashboard_daily_metrics(
            start_date=_parse_date(start_date),
            end_date=_parse_date(end_date),
        )
    except Exception as e:
        logger.error("get_dashboard_daily_metrics_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при расчете ежедневных метрик"
        )


@router.get("/dashboard/channels", response_model=list[ChannelPerformanceItem])
def get_dashboard_channel_performance(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    service = AnalyticsService(db)
    try:
        return service.get_channel_performance(
            start_date=_parse_date(start_date),
            end_date=_parse_date(end_date),
        )
    except Exception as e:
        logger.error("get_dashboard_channel_performance_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при расчете метрик каналов"
        )

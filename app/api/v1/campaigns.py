"""
DeepCalm — Campaigns API

CRUD endpoints для управления кампаниями.
Следует DEEP-CALM-MVP-BLUEPRINT.md
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.core.db import get_db
from app.models.campaign import Campaign
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/campaigns", response_model=CampaignListResponse)
def get_campaigns(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """
    Получить список кампаний с пагинацией.

    Args:
        page: Номер страницы (начиная с 1)
        page_size: Количество элементов на странице (1-100)
        status: Фильтр по статусу (draft|active|paused|stopped)
        db: Database session

    Returns:
        CampaignListResponse с пагинацией

    Examples:
        >>> GET /api/v1/campaigns?page=1&page_size=20&status=active
    """
    logger.info(
        "campaigns_list_requested",
        page=page,
        page_size=page_size,
        status=status
    )

    # Базовый запрос
    query = db.query(Campaign)

    # Фильтр по статусу
    if status:
        query = query.filter(Campaign.status == status)

    # Подсчёт общего количества
    total = query.count()

    # Пагинация
    offset = (page - 1) * page_size
    campaigns = query.order_by(Campaign.created_at.desc()).offset(offset).limit(page_size).all()

    logger.info(
        "campaigns_list_returned",
        total=total,
        page=page,
        returned=len(campaigns)
    )

    return CampaignListResponse(
        items=campaigns,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новую кампанию.

    Args:
        campaign: Данные кампании (CampaignCreate)
        db: Database session

    Returns:
        Созданная кампания (CampaignResponse)

    Raises:
        HTTPException: 400 если валидация не прошла

    Examples:
        >>> POST /api/v1/campaigns
        >>> {
        >>>   "title": "Запуск сентябрь — Релакс",
        >>>   "sku": "RELAX-60",
        >>>   "budget_rub": 15000,
        >>>   "channels": ["vk", "direct"]
        >>> }
    """
    logger.info(
        "campaign_create_started",
        title=campaign.title,
        sku=campaign.sku,
        budget=campaign.budget_rub,
        channels=campaign.channels
    )

    # Создаём Campaign из Pydantic схемы
    db_campaign = Campaign(**campaign.model_dump())

    try:
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)

        logger.info(
            "campaign_created",
            campaign_id=str(db_campaign.id),
            title=db_campaign.title,
            status="success"
        )

        return db_campaign

    except Exception as e:
        db.rollback()
        logger.error(
            "campaign_create_failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create campaign")


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Получить кампанию по ID.

    Args:
        campaign_id: UUID кампании
        db: Database session

    Returns:
        CampaignResponse

    Raises:
        HTTPException: 404 если кампания не найдена

    Examples:
        >>> GET /api/v1/campaigns/550e8400-e29b-41d4-a716-446655440000
    """
    logger.info("campaign_get_requested", campaign_id=str(campaign_id))

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        logger.warning("campaign_not_found", campaign_id=str(campaign_id))
        raise HTTPException(status_code=404, detail="Campaign not found")

    logger.info("campaign_returned", campaign_id=str(campaign_id))
    return campaign


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: UUID,
    campaign_update: CampaignUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить кампанию (частичное обновление).

    Args:
        campaign_id: UUID кампании
        campaign_update: Обновляемые поля
        db: Database session

    Returns:
        Обновлённая кампания (CampaignResponse)

    Raises:
        HTTPException: 404 если кампания не найдена

    Examples:
        >>> PATCH /api/v1/campaigns/550e8400-e29b-41d4-a716-446655440000
        >>> {
        >>>   "status": "active",
        >>>   "budget_rub": 20000
        >>> }
    """
    logger.info(
        "campaign_update_started",
        campaign_id=str(campaign_id),
        updates=campaign_update.model_dump(exclude_unset=True)
    )

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        logger.warning("campaign_not_found", campaign_id=str(campaign_id))
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Обновляем только переданные поля
    update_data = campaign_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(campaign, key, value)

    try:
        db.commit()
        db.refresh(campaign)

        logger.info(
            "campaign_updated",
            campaign_id=str(campaign_id),
            status="success"
        )

        return campaign

    except Exception as e:
        db.rollback()
        logger.error(
            "campaign_update_failed",
            campaign_id=str(campaign_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to update campaign")


@router.delete("/campaigns/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Удалить кампанию.

    Args:
        campaign_id: UUID кампании
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: 404 если кампания не найдена

    Examples:
        >>> DELETE /api/v1/campaigns/550e8400-e29b-41d4-a716-446655440000
    """
    logger.info("campaign_delete_requested", campaign_id=str(campaign_id))

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        logger.warning("campaign_not_found", campaign_id=str(campaign_id))
        raise HTTPException(status_code=404, detail="Campaign not found")

    try:
        db.delete(campaign)
        db.commit()

        logger.info(
            "campaign_deleted",
            campaign_id=str(campaign_id),
            status="success"
        )

    except Exception as e:
        db.rollback()
        logger.error(
            "campaign_delete_failed",
            campaign_id=str(campaign_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete campaign")

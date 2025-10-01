"""
DeepCalm — Creatives API

Управление креативами и генерация через LLM.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import structlog

from app.core.db import get_db
from app.models.campaign import Campaign
from app.models.creative import Creative
from app.schemas.creative import (
    CreativeCreate,
    CreativeResponse,
    CreativeListResponse,
    CreativeGenerateRequest
)
from app.services.creative_generator import CreativeGenerator

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/creatives", response_model=CreativeListResponse)
def get_creatives(
    campaign_id: Optional[UUID] = Query(None, description="Фильтр по кампании"),
    db: Session = Depends(get_db)
):
    """
    Получить список креативов.

    Args:
        campaign_id: Фильтр по ID кампании (опционально)
        db: Database session

    Returns:
        CreativeListResponse
    """
    logger.info("creatives_list_requested", campaign_id=str(campaign_id) if campaign_id else None)

    query = db.query(Creative)

    if campaign_id:
        query = query.filter(Creative.campaign_id == campaign_id)

    creatives = query.order_by(Creative.created_at.desc()).all()
    total = query.count()

    logger.info("creatives_list_returned", total=total)

    return CreativeListResponse(items=creatives, total=total)


@router.post("/creatives", response_model=CreativeResponse, status_code=201)
def create_creative(
    creative: CreativeCreate,
    db: Session = Depends(get_db)
):
    """
    Создать креатив вручную.

    Args:
        creative: Данные креатива
        db: Database session

    Returns:
        CreativeResponse

    Raises:
        HTTPException: 404 если кампания не найдена
    """
    logger.info(
        "creative_create_started",
        campaign_id=str(creative.campaign_id),
        variant=creative.variant
    )

    # Проверяем что кампания существует
    campaign = db.query(Campaign).filter(Campaign.id == creative.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Создаём креатив
    db_creative = Creative(**creative.model_dump())

    try:
        db.add(db_creative)
        db.commit()
        db.refresh(db_creative)

        logger.info(
            "creative_created",
            creative_id=str(db_creative.id),
            status="success"
        )

        return db_creative

    except Exception as e:
        db.rollback()
        logger.error("creative_create_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create creative")


@router.post("/creatives/generate", response_model=list[CreativeResponse], status_code=201)
def generate_creatives(
    request: CreativeGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Сгенерировать креативы через LLM (mock для MVP).

    Args:
        request: Параметры генерации
        db: Database session

    Returns:
        Список созданных креативов

    Raises:
        HTTPException: 404 если кампания не найдена

    Examples:
        >>> POST /api/v1/creatives/generate
        >>> {
        >>>   "campaign_id": "550e8400-e29b-41d4-a716-446655440001",
        >>>   "count": 3
        >>> }
    """
    logger.info(
        "creatives_generate_started",
        campaign_id=str(request.campaign_id),
        count=request.count
    )

    # Проверяем кампанию
    campaign = db.query(Campaign).filter(Campaign.id == request.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Генерируем креативы
    generator = CreativeGenerator()
    creatives_data = generator.generate_creatives(
        campaign=campaign,
        count=request.count,
        temperature=request.temperature
    )

    # Сохраняем в БД
    created_creatives = []
    try:
        for creative_data in creatives_data:
            db_creative = Creative(
                campaign_id=campaign.id,
                **creative_data
            )
            db.add(db_creative)
            created_creatives.append(db_creative)

        db.commit()

        # Refresh для получения ID
        for creative in created_creatives:
            db.refresh(creative)

        logger.info(
            "creatives_generated",
            campaign_id=str(campaign.id),
            count=len(created_creatives),
            status="success"
        )

        return created_creatives

    except Exception as e:
        db.rollback()
        logger.error(
            "creatives_generate_failed",
            campaign_id=str(campaign.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to generate creatives")


@router.get("/creatives/{creative_id}", response_model=CreativeResponse)
def get_creative(
    creative_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Получить креатив по ID.

    Args:
        creative_id: UUID креатива
        db: Database session

    Returns:
        CreativeResponse

    Raises:
        HTTPException: 404 если не найден
    """
    logger.info("creative_get_requested", creative_id=str(creative_id))

    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        logger.warning("creative_not_found", creative_id=str(creative_id))
        raise HTTPException(status_code=404, detail="Creative not found")

    return creative


@router.delete("/creatives/{creative_id}", status_code=204)
def delete_creative(
    creative_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Удалить креатив.

    Args:
        creative_id: UUID креатива
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException: 404 если не найден
    """
    logger.info("creative_delete_requested", creative_id=str(creative_id))

    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        logger.warning("creative_not_found", creative_id=str(creative_id))
        raise HTTPException(status_code=404, detail="Creative not found")

    try:
        db.delete(creative)
        db.commit()

        logger.info("creative_deleted", creative_id=str(creative_id), status="success")

    except Exception as e:
        db.rollback()
        logger.error(
            "creative_delete_failed",
            creative_id=str(creative_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete creative")

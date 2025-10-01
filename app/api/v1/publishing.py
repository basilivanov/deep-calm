"""
API endpoints для публикации креативов на рекламные платформы
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.publishing import (
    PauseResponse,
    PlacementInfo,
    PublishingStatusResponse,
    PublishRequest,
    PublishResponse,
)
from app.services.publishing_service import PublishingService

logger = structlog.get_logger()
router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.post("/publish", response_model=PublishResponse, status_code=status.HTTP_201_CREATED)
def publish_campaign(
    request: PublishRequest,
    db: Session = Depends(get_db)
):
    """
    Публикует кампанию на указанные рекламные платформы

    - **campaign_id**: ID кампании для публикации
    - **channels**: Список каналов (vk/direct/avito). Если не указано - публикуем во все каналы кампании
    """
    logger.info("publish_campaign_request", campaign_id=str(request.campaign_id), channels=request.channels)

    service = PublishingService(db)

    try:
        result = service.publish_campaign(
            campaign_id=request.campaign_id,
            channels=request.channels
        )

        placements_info = [
            PlacementInfo(
                placement_id=p.id,
                channel=p.channel_code,
                creative_variant=p.creative.variant,
                external_id=p.external_campaign_id,
                status=p.status,
                created_at=p.published_at
            )
            for p in result["placements"]
        ]

        response = PublishResponse(
            campaign_id=request.campaign_id,
            placements=placements_info,
            success_count=result["success_count"],
            failed_count=result["failed_count"],
            message=f"Успешно опубликовано: {result['success_count']}, ошибок: {result['failed_count']}"
        )

        logger.info(
            "publish_campaign_success",
            campaign_id=str(request.campaign_id),
            success_count=result["success_count"],
            failed_count=result["failed_count"]
        )

        return response

    except ValueError as e:
        logger.error("publish_campaign_validation_error", campaign_id=str(request.campaign_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("publish_campaign_error", campaign_id=str(request.campaign_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при публикации кампании"
        )


@router.get("/status/{campaign_id}", response_model=PublishingStatusResponse)
def get_publishing_status(
    campaign_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Получает статус публикации кампании

    - **campaign_id**: ID кампании
    """
    logger.info("get_publishing_status_request", campaign_id=str(campaign_id))

    service = PublishingService(db)

    try:
        result = service.get_campaign_status(campaign_id)

        placements_info = [
            PlacementInfo(
                placement_id=p.id,
                channel=p.channel_code,
                creative_variant=p.creative.variant,
                external_id=p.external_campaign_id,
                status=p.status,
                created_at=p.published_at
            )
            for p in result["placements"]
        ]

        response = PublishingStatusResponse(
            campaign_id=campaign_id,
            campaign_title=result["campaign"].title,
            total_placements=result["total_placements"],
            active_placements=result["active_placements"],
            paused_placements=result["paused_placements"],
            failed_placements=result["failed_placements"],
            placements=placements_info
        )

        logger.info(
            "get_publishing_status_success",
            campaign_id=str(campaign_id),
            total_placements=result["total_placements"]
        )

        return response

    except ValueError as e:
        logger.error("get_publishing_status_validation_error", campaign_id=str(campaign_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_publishing_status_error", campaign_id=str(campaign_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статуса публикации"
        )


@router.post("/pause/{campaign_id}", response_model=PauseResponse)
def pause_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Приостанавливает все размещения кампании на всех платформах

    - **campaign_id**: ID кампании
    """
    logger.info("pause_campaign_request", campaign_id=str(campaign_id))

    service = PublishingService(db)

    try:
        result = service.pause_campaign(campaign_id)

        response = PauseResponse(
            campaign_id=campaign_id,
            paused_count=result["paused_count"],
            failed_count=result["failed_count"],
            message=f"Приостановлено: {result['paused_count']}, ошибок: {result['failed_count']}"
        )

        logger.info(
            "pause_campaign_success",
            campaign_id=str(campaign_id),
            paused_count=result["paused_count"],
            failed_count=result["failed_count"]
        )

        return response

    except ValueError as e:
        logger.error("pause_campaign_validation_error", campaign_id=str(campaign_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("pause_campaign_error", campaign_id=str(campaign_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при приостановке кампании"
        )

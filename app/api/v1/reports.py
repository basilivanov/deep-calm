"""
DeepCalm — Reports API

Endpoints для генерации и управления отчетами.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import structlog

from app.core.db import get_db
from app.services.weekly_reports import WeeklyReportsService
from app.services.scheduler import scheduler
from app.schemas.reports import (
    WeeklyReportResponse,
    ReportGenerationRequest,
    ReportStatusResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_reports_service(db: Session = Depends(get_db)) -> WeeklyReportsService:
    """Dependency для Reports Service"""
    return WeeklyReportsService(db)


@router.post("/reports/weekly/generate", response_model=WeeklyReportResponse)
def generate_weekly_report(
    request: Optional[ReportGenerationRequest] = None,
    reports: WeeklyReportsService = Depends(get_reports_service)
):
    """
    Генерация еженедельного отчета

    Создает детальный отчет с AI анализом за указанный период.
    """
    weeks_back = request.weeks_back if request else 1

    logger.info("generate_weekly_report_request", weeks_back=weeks_back)

    try:
        report = reports.generate_weekly_report(weeks_back)

        if report.get("status") in ["disabled", "error"]:
            raise HTTPException(
                status_code=400,
                detail=report.get("message", "Ошибка генерации отчета")
            )

        return WeeklyReportResponse(**report)

    except Exception as e:
        logger.error("report_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка генерации отчета")


@router.get("/reports/weekly/preview")
def preview_weekly_data(
    weeks_back: int = 1,
    reports: WeeklyReportsService = Depends(get_reports_service)
):
    """
    Превью данных для отчета

    Возвращает сырые данные без AI анализа для быстрого просмотра.
    """
    logger.info("preview_weekly_data", weeks_back=weeks_back)

    try:
        data = reports.get_weekly_data(weeks_back)
        return data

    except Exception as e:
        logger.error("preview_data_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@router.get("/reports/status", response_model=ReportStatusResponse)
def get_reports_status(
    reports: WeeklyReportsService = Depends(get_reports_service)
):
    """
    Статус системы отчетов

    Проверяет настройки и готовность к генерации отчетов.
    """
    try:
        status = {
            "reports_enabled": reports.is_reports_enabled(),
            "reports_email": reports.get_reports_email(),
            "ai_available": bool(reports.ai_analyst._settings.get("openai_api_key")),
            "last_check": "2025-10-01T20:50:00Z"  # TODO: добавить реальную проверку
        }

        if not status["reports_enabled"]:
            status["message"] = "Отчеты отключены в настройках"
        elif not status["ai_available"]:
            status["message"] = "OpenAI API не настроен"
        else:
            status["message"] = "Система отчетов готова к работе"

        return ReportStatusResponse(**status)

    except Exception as e:
        logger.error("reports_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка проверки статуса")


@router.post("/reports/weekly/email")
def send_weekly_report_email(
    background_tasks: BackgroundTasks,
    request: Optional[ReportGenerationRequest] = None,
    reports: WeeklyReportsService = Depends(get_reports_service)
):
    """
    Отправка отчета по email

    Генерирует отчет и отправляет на email из настроек.
    """
    weeks_back = request.weeks_back if request else 1

    logger.info("send_weekly_report_email", weeks_back=weeks_back)

    if not reports.is_reports_enabled():
        raise HTTPException(
            status_code=400,
            detail="Отчеты отключены в настройках"
        )

    # Добавляем задачу в background
    background_tasks.add_task(
        _send_report_background,
        reports,
        weeks_back
    )

    return {
        "status": "scheduled",
        "message": f"Отчет будет отправлен на {reports.get_reports_email()}",
        "weeks_back": weeks_back
    }


def _send_report_background(reports: WeeklyReportsService, weeks_back: int):
    """Background задача для отправки отчета"""
    try:
        logger.info("background_report_generation_started", weeks_back=weeks_back)

        # Генерируем отчет
        report = reports.generate_weekly_report(weeks_back)

        if report.get("status") in ["disabled", "error"]:
            logger.error("background_report_failed", status=report.get("status"))
            return

        # Форматируем для email
        email_content = reports.format_report_for_email(report)

        # TODO: Интеграция с email сервисом (SendGrid, AWS SES, etc)
        # Пока просто логируем
        logger.info(
            "report_email_content_generated",
            report_id=report["id"],
            email=reports.get_reports_email(),
            content_length=len(email_content)
        )

        # В реальном приложении здесь был бы код отправки email:
        # send_email(
        #     to=reports.get_reports_email(),
        #     subject=f"📊 Еженедельный отчет DeepCalm {report['period']['start_date'][:10]}",
        #     body=email_content
        # )

        logger.info("background_report_completed", report_id=report["id"])

    except Exception as e:
        logger.error("background_report_error", error=str(e))


@router.post("/reports/test")
def test_report_generation(
    reports: WeeklyReportsService = Depends(get_reports_service)
):
    """
    Тест генерации отчета

    Быстрый тест системы отчетов без отправки email.
    """
    try:
        # Проверяем статус
        if not reports.is_reports_enabled():
            return {
                "status": "disabled",
                "message": "Отчеты отключены. Включите в настройках: reports_enabled = true"
            }

        # Проверяем AI
        if not reports.ai_analyst._settings.get("openai_api_key"):
            return {
                "status": "no_ai",
                "message": "OpenAI API ключ не настроен. Добавьте в настройки: openai_api_key"
            }

        # Получаем preview данных
        preview_data = reports.get_weekly_data(1)

        return {
            "status": "ok",
            "message": "Система отчетов готова к работе",
            "preview": {
                "total_leads": preview_data["summary"]["total_leads"],
                "total_conversions": preview_data["summary"]["total_conversions"],
                "active_campaigns": preview_data["summary"]["active_campaigns"],
                "reports_email": reports.get_reports_email()
            }
        }

    except Exception as e:
        logger.error("test_report_failed", error=str(e))
        return {
            "status": "error",
            "message": f"Ошибка тестирования: {str(e)}"
        }


@router.get("/reports/scheduler/status")
def get_scheduler_status():
    """
    Статус планировщика задач

    Показывает расписание автоматических отчетов.
    """
    try:
        status = scheduler.get_status()
        return status
    except Exception as e:
        logger.error("scheduler_status_failed", error=str(e))
        return {
            "running": False,
            "error": str(e)
        }
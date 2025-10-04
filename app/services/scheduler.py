"""
DeepCalm — Task Scheduler

APScheduler для автоматических задач (отчеты, анализ).
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from app.core.db import SessionLocal
from app.services.weekly_reports import WeeklyReportsService

logger = structlog.get_logger(__name__)


class DeepCalmScheduler:
    """Планировщик задач DeepCalm"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """Настройка запланированных задач"""

        # Еженедельные отчеты (каждый понедельник в 9:00)
        self.scheduler.add_job(
            func=self._generate_weekly_report,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_report',
            name='Генерация еженедельного отчета',
            replace_existing=True
        )

        # Ежедневная проверка кампаний (каждый день в 10:00)
        self.scheduler.add_job(
            func=self._daily_campaign_check,
            trigger=CronTrigger(hour=10, minute=0),
            id='daily_check',
            name='Ежедневная проверка кампаний',
            replace_existing=True
        )

        logger.info("scheduler_jobs_configured", jobs_count=len(self.scheduler.get_jobs()))

    async def _generate_weekly_report(self):
        """Автоматическая генерация еженедельного отчета"""
        try:
            logger.info("scheduled_weekly_report_started")

            # Создаем сессию БД
            db = SessionLocal()
            try:
                reports_service = WeeklyReportsService(db)

                # Проверяем что отчеты включены
                if not reports_service.is_reports_enabled():
                    logger.info("weekly_reports_disabled_skipping")
                    return

                # Генерируем отчет
                report = reports_service.generate_weekly_report(weeks_back=1)

                if report.get("status") == "error":
                    logger.error("scheduled_report_failed", error=report.get("message"))
                    return

                # Форматируем для email
                email_content = reports_service.format_report_for_email(report)

                # TODO: Отправка email
                # await send_email(
                #     to=reports_service.get_reports_email(),
                #     subject=f"📊 Еженедельный отчет DeepCalm {report['period']['start_date'][:10]}",
                #     body=email_content
                # )

                logger.info(
                    "scheduled_weekly_report_completed",
                    report_id=report["id"],
                    email=reports_service.get_reports_email()
                )

            finally:
                db.close()

        except Exception as e:
            logger.error("scheduled_weekly_report_error", error=str(e))

    async def _daily_campaign_check(self):
        """Ежедневная проверка кампаний на проблемы"""
        try:
            logger.info("scheduled_daily_check_started")

            db = SessionLocal()
            try:
                reports_service = WeeklyReportsService(db)

                # Получаем данные за последние 7 дней
                data = reports_service.get_weekly_data(weeks_back=1)

                # Проверяем кампании, требующие внимания
                needs_attention = data.get("needs_attention", [])

                if needs_attention:
                    logger.warning(
                        "campaigns_need_attention",
                        count=len(needs_attention),
                        campaigns=[c["title"] for c in needs_attention[:3]]
                    )

                    # TODO: Отправка уведомления в Slack/Telegram
                    # await send_alert(f"⚠️ {len(needs_attention)} кампаний требуют внимания")

                else:
                    logger.info("all_campaigns_performing_well")

            finally:
                db.close()

        except Exception as e:
            logger.error("scheduled_daily_check_error", error=str(e))

    def start(self):
        """Запуск планировщика"""
        try:
            self.scheduler.start()
            logger.info("scheduler_started", jobs=len(self.scheduler.get_jobs()))

            # Логируем расписание
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time
                logger.info(
                    "scheduled_job",
                    job_id=job.id,
                    job_name=job.name,
                    next_run=next_run.isoformat() if next_run else "N/A"
                )

        except Exception as e:
            logger.error("scheduler_start_failed", error=str(e))

    def stop(self):
        """Остановка планировщика"""
        try:
            self.scheduler.shutdown()
            logger.info("scheduler_stopped")
        except Exception as e:
            logger.error("scheduler_stop_failed", error=str(e))

    def get_status(self) -> dict:
        """Получить статус планировщика"""
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "running": self.scheduler.running,
            "jobs_count": len(self.scheduler.get_jobs()),
            "jobs": jobs_info
        }


# Глобальный экземпляр планировщика
scheduler = DeepCalmScheduler()
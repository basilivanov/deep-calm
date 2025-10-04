"""
DeepCalm — Weekly Reports Service

Автоматическая генерация еженедельных отчетов через AI Analyst.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.models.setting import Setting
from app.models.campaign import Campaign
from app.models.creative import Creative
from app.models.lead import Lead
from app.models.conversion import Conversion
from app.services.ai_analyst import AIAnalystService

logger = structlog.get_logger(__name__)


class WeeklyReportsService:
    """Сервис автоматических еженедельных отчетов"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_analyst = AIAnalystService(db)
        self._settings = {}
        self._load_settings()

    def _load_settings(self):
        """Загружает настройки отчетов"""
        operational_settings = self.db.query(Setting).filter(
            Setting.category == "operational"
        ).all()

        for setting in operational_settings:
            if setting.value_type == "bool":
                value = setting.value.lower() in ('true', '1', 'yes', 'on')
            elif setting.value_type == "int":
                value = int(setting.value)
            elif setting.value_type == "float":
                value = float(setting.value)
            else:
                value = setting.value

            self._settings[setting.key] = value

        logger.info("reports_settings_loaded", count=len(self._settings))

    def is_reports_enabled(self) -> bool:
        """Проверяет включены ли отчеты"""
        return self._settings.get("reports_enabled", False)

    def get_reports_email(self) -> str:
        """Получает email для отчетов"""
        return self._settings.get("reports_email", "admin@deepcalm.local")

    def get_weekly_data(self, weeks_back: int = 1) -> Dict[str, Any]:
        """Собирает данные за последние N недель"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)

        logger.info("collecting_weekly_data", start_date=start_date, end_date=end_date)

        # Активные кампании
        campaigns = self.db.query(Campaign).filter(
            Campaign.status.in_(["active", "paused"])
        ).all()

        # Лиды за период
        leads = self.db.query(Lead).filter(
            Lead.created_at >= start_date,
            Lead.created_at <= end_date
        ).all()

        # Конверсии за период
        conversions = self.db.query(Conversion).filter(
            Conversion.converted_at >= start_date,
            Conversion.converted_at <= end_date
        ).all()

        # Агрегированные метрики
        total_leads = len(leads)
        total_conversions = len(conversions)
        total_revenue = sum(c.revenue_rub for c in conversions)
        conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0

        # Метрики по кампаниям
        campaign_metrics = []
        for campaign in campaigns:
            campaign_leads = [l for l in leads if campaign.title.lower() in (l.utm_campaign or "").lower()]
            campaign_conversions = [c for c in conversions if c.campaign_id == campaign.id]

            campaign_revenue = sum(c.revenue_rub for c in campaign_conversions)
            campaign_spend = campaign.spent_rub or 0
            campaign_roas = (campaign_revenue / campaign_spend) if campaign_spend > 0 else 0
            campaign_cac = (campaign_spend / len(campaign_conversions)) if campaign_conversions else 0

            campaign_metrics.append({
                "id": campaign.id,
                "title": campaign.title,
                "sku": campaign.sku,
                "status": campaign.status,
                "leads": len(campaign_leads),
                "conversions": len(campaign_conversions),
                "revenue": campaign_revenue,
                "spend": campaign_spend,
                "roas": round(campaign_roas, 2),
                "cac": round(campaign_cac, 2),
                "target_cac": campaign.target_cac_rub,
                "target_roas": campaign.target_roas
            })

        # Сортируем по убыванию ROAS
        campaign_metrics.sort(key=lambda x: x["roas"], reverse=True)

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "weeks": weeks_back
            },
            "summary": {
                "total_leads": total_leads,
                "total_conversions": total_conversions,
                "total_revenue": total_revenue,
                "conversion_rate": round(conversion_rate, 2),
                "active_campaigns": len(campaigns)
            },
            "campaigns": campaign_metrics,
            "top_performers": campaign_metrics[:3] if campaign_metrics else [],
            "needs_attention": [c for c in campaign_metrics if c["roas"] < c.get("target_roas", 2.0)]
        }

    def generate_ai_summary(self, weekly_data: Dict[str, Any]) -> str:
        """Генерирует AI резюме недельных данных"""
        try:
            prompt = self._create_weekly_report_prompt(weekly_data)

            # Используем AI Analyst для генерации отчета
            response = self.ai_analyst.openai_client.chat.completions.create(
                model=self.ai_analyst._settings.get("ai_model", "gpt-4"),
                messages=[
                    {"role": "system", "content": self._create_weekly_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Более консервативно для отчетов
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error("ai_summary_failed", error=str(e))
            return "❌ Не удалось сгенерировать AI анализ. Проверьте настройки OpenAI API."

    def _create_weekly_system_prompt(self) -> str:
        """Системный промпт для еженедельных отчетов"""
        return """Ты создаешь еженедельный отчет для руководителя массажного салона о performance маркетинге.

ФОРМАТ ОТЧЕТА:
📊 ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ DEEPCALM

📈 КЛЮЧЕВЫЕ МЕТРИКИ
[Краткие выводы по метрикам]

🏆 ТОП-КАМПАНИИ
[3 лучшие кампании с причинами успеха]

⚠️ ТРЕБУЮТ ВНИМАНИЯ
[Кампании с проблемами и рекомендации]

🎯 РЕКОМЕНДАЦИИ НА СЛЕДУЮЩУЮ НЕДЕЛЮ
[3-5 конкретных действий]

💰 ФИНАНСОВЫЕ ВЫВОДЫ
[ROI, бюджетные рекомендации]

СТИЛЬ:
- Деловой, но понятный
- Конкретные цифры и проценты
- Actionable рекомендации
- Фокус на ROI и прибыльности"""

    def _create_weekly_report_prompt(self, data: Dict[str, Any]) -> str:
        """Создает промпт с данными недели"""
        summary = data["summary"]
        campaigns = data["campaigns"]
        top_performers = data["top_performers"]
        needs_attention = data["needs_attention"]

        prompt = f"""ДАННЫЕ ЗА НЕДЕЛЮ ({data["period"]["start_date"][:10]} - {data["period"]["end_date"][:10]}):

ОБЩИЕ МЕТРИКИ:
- Лиды: {summary["total_leads"]}
- Конверсии: {summary["total_conversions"]}
- Конверсия: {summary["conversion_rate"]}%
- Выручка: {summary["total_revenue"]:,.0f} ₽
- Активные кампании: {summary["active_campaigns"]}

ТОП-3 КАМПАНИИ:"""

        for i, campaign in enumerate(top_performers, 1):
            prompt += f"""
{i}. {campaign["title"]} ({campaign["sku"]})
   - ROAS: {campaign["roas"]} (цель: {campaign.get("target_roas", "N/A")})
   - CAC: {campaign["cac"]:,.0f} ₽ (цель: {campaign.get("target_cac", "N/A")} ₽)
   - Лиды: {campaign["leads"]}, Конверсии: {campaign["conversions"]}
   - Выручка: {campaign["revenue"]:,.0f} ₽"""

        if needs_attention:
            prompt += f"\n\nПРОБЛЕМНЫЕ КАМПАНИИ:"
            for campaign in needs_attention[:3]:
                prompt += f"""
- {campaign["title"]}: ROAS {campaign["roas"]} (ниже цели {campaign.get("target_roas", 2.0)})"""

        prompt += "\n\nСоздай comprehensive еженедельный отчет с анализом и рекомендациями."

        return prompt

    def generate_weekly_report(self, weeks_back: int = 1) -> Dict[str, Any]:
        """Генерирует полный еженедельный отчет"""
        if not self.is_reports_enabled():
            logger.warning("weekly_reports_disabled")
            return {
                "status": "disabled",
                "message": "Еженедельные отчеты отключены в настройках"
            }

        try:
            logger.info("generating_weekly_report", weeks_back=weeks_back)

            # Собираем данные
            weekly_data = self.get_weekly_data(weeks_back)

            # Генерируем AI анализ
            ai_summary = self.generate_ai_summary(weekly_data)

            # Формируем отчет
            report = {
                "id": f"weekly_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generated_at": datetime.now().isoformat(),
                "period": weekly_data["period"],
                "summary": weekly_data["summary"],
                "ai_analysis": ai_summary,
                "detailed_data": {
                    "top_performers": weekly_data["top_performers"],
                    "needs_attention": weekly_data["needs_attention"],
                    "all_campaigns": weekly_data["campaigns"]
                },
                "settings": {
                    "reports_email": self.get_reports_email(),
                    "auto_generated": True
                }
            }

            logger.info("weekly_report_generated",
                       report_id=report["id"],
                       campaigns_count=len(weekly_data["campaigns"]),
                       total_revenue=weekly_data["summary"]["total_revenue"])

            return report

        except Exception as e:
            logger.error("weekly_report_generation_failed", error=str(e))
            return {
                "status": "error",
                "message": f"Ошибка генерации отчета: {str(e)}"
            }

    def format_report_for_email(self, report: Dict[str, Any]) -> str:
        """Форматирует отчет для отправки по email"""
        if report.get("status") in ["disabled", "error"]:
            return report.get("message", "Неизвестная ошибка")

        summary = report["summary"]
        period = report["period"]

        email_content = f"""
📊 ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ DEEPCALM

📅 Период: {period["start_date"][:10]} - {period["end_date"][:10]}

📈 КЛЮЧЕВЫЕ МЕТРИКИ:
• Лиды: {summary["total_leads"]}
• Конверсии: {summary["total_conversions"]} (CR: {summary["conversion_rate"]}%)
• Выручка: {summary["total_revenue"]:,.0f} ₽
• Активные кампании: {summary["active_campaigns"]}

{report["ai_analysis"]}

🏆 ТОП-КАМПАНИИ:
"""

        for i, campaign in enumerate(report["detailed_data"]["top_performers"], 1):
            email_content += f"""
{i}. {campaign["title"]} ({campaign["sku"]})
   ROAS: {campaign["roas"]} | CAC: {campaign["cac"]:,.0f} ₽
   Лиды: {campaign["leads"]} | Конверсии: {campaign["conversions"]}
   Выручка: {campaign["revenue"]:,.0f} ₽
"""

        if report["detailed_data"]["needs_attention"]:
            email_content += "\n⚠️ ТРЕБУЮТ ВНИМАНИЯ:\n"
            for campaign in report["detailed_data"]["needs_attention"][:3]:
                email_content += f"• {campaign['title']}: ROAS {campaign['roas']} (цель: {campaign.get('target_roas', 'N/A')})\n"

        email_content += f"""
---
🤖 Автоматический отчет DeepCalm AI
📧 Отправлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
⚙️ Настройки отчетов: /settings
"""

        return email_content
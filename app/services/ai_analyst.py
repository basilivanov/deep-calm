"""
DeepCalm — AI Analyst Service

GPT-4 анализ кампаний и генерация рекомендаций.
Использует настройки из Settings API.
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
import openai
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.setting import Setting
from app.models.campaign import Campaign
from app.models.creative import Creative
from app.models.lead import Lead
from app.models.conversion import Conversion

logger = structlog.get_logger(__name__)


class AIAnalystService:
    """Сервис AI анализа кампаний"""

    def __init__(self, db: Session):
        self.db = db
        self._openai_client = None
        self._settings = {}
        self._load_settings()

    def _load_settings(self):
        """Загружает настройки AI из Settings API"""
        ai_settings = self.db.query(Setting).filter(Setting.category == "ai").all()

        for setting in ai_settings:
            # Конвертируем в правильный тип
            if setting.value_type == "int":
                value = int(setting.value)
            elif setting.value_type == "float":
                value = float(setting.value)
            elif setting.value_type == "bool":
                value = setting.value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = setting.value

            self._settings[setting.key] = value

        logger.info("ai_settings_loaded", count=len(self._settings))

    @property
    def openai_client(self):
        """Ленивая инициализация OpenAI клиента"""
        if self._openai_client is None:
            api_key = self._settings.get("openai_api_key")
            if not api_key or api_key == "sk-your-openai-key-here":
                raise ValueError("OpenAI API ключ не настроен. Обновите настройку openai_api_key")

            self._openai_client = openai.OpenAI(api_key=api_key)

        return self._openai_client

    def get_campaign_data(self, campaign_id: int) -> Dict[str, Any]:
        """Получает данные кампании для анализа"""
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Кампания {campaign_id} не найдена")

        # Получаем креативы
        creatives = self.db.query(Creative).filter(Creative.campaign_id == campaign_id).all()

        # Получаем лиды за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        leads = self.db.query(Lead).filter(
            Lead.utm_campaign.ilike(f"%{campaign.title}%"),
            Lead.created_at >= thirty_days_ago
        ).all()

        # Получаем конверсии
        conversions = self.db.query(Conversion).filter(
            Conversion.campaign_id == campaign_id
        ).all()

        # Рассчитываем метрики
        total_leads = len(leads)
        total_conversions = len(conversions)
        conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0
        total_revenue = sum(c.revenue_rub for c in conversions)
        total_spend = campaign.spent_rub or 0
        roas = (total_revenue / total_spend) if total_spend > 0 else 0
        cac = (total_spend / total_conversions) if total_conversions > 0 else 0

        return {
            "campaign": {
                "id": campaign.id,
                "title": campaign.title,
                "sku": campaign.sku,
                "status": campaign.status,
                "budget_rub": campaign.budget_rub,
                "spent_rub": total_spend,
                "target_cac_rub": campaign.target_cac_rub,
                "target_roas": campaign.target_roas,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None
            },
            "creatives": [
                {
                    "id": c.id,
                    "variant": c.variant,
                    "title": c.title,
                    "body": c.body,
                    "status": c.status
                } for c in creatives
            ],
            "metrics": {
                "total_leads": total_leads,
                "total_conversions": total_conversions,
                "conversion_rate": round(conversion_rate, 2),
                "total_revenue": total_revenue,
                "total_spend": total_spend,
                "roas": round(roas, 2),
                "cac": round(cac, 2),
                "period_days": 30
            },
            "targets": {
                "target_cac": campaign.target_cac_rub,
                "target_roas": campaign.target_roas,
                "max_budget": self._settings.get("max_campaign_budget", 100000),
                "min_roas_threshold": self._get_financial_setting("min_roas_threshold", 2.0)
            }
        }

    def _get_financial_setting(self, key: str, default: Any) -> Any:
        """Получает финансовую настройку"""
        setting = self.db.query(Setting).filter(
            Setting.key == key,
            Setting.category == "financial"
        ).first()

        if not setting:
            return default

        if setting.value_type == "float":
            return float(setting.value)
        elif setting.value_type == "int":
            return int(setting.value)
        else:
            return setting.value

    def analyze_campaign(self, campaign_id: int, user_question: Optional[str] = None) -> Dict[str, Any]:
        """Анализирует кампанию через GPT-4"""
        try:
            # Получаем данные кампании
            campaign_data = self.get_campaign_data(campaign_id)

            # Формируем промпт для GPT-4
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(campaign_data, user_question)

            # Делаем запрос к OpenAI
            response = self.openai_client.chat.completions.create(
                model=self._settings.get("ai_model", "gpt-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self._settings.get("ai_temperature", 0.3),
                max_tokens=self._settings.get("ai_max_tokens", 2000)
            )

            analysis_text = response.choices[0].message.content

            # Логируем использование токенов
            usage = response.usage
            logger.info(
                "openai_analysis_completed",
                campaign_id=campaign_id,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )

            return {
                "campaign_id": campaign_id,
                "analysis": analysis_text,
                "metrics": campaign_data["metrics"],
                "recommendations": self._extract_recommendations(analysis_text),
                "generated_at": datetime.now().isoformat(),
                "token_usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            }

        except Exception as e:
            logger.error("ai_analysis_failed", campaign_id=campaign_id, error=str(e))
            raise

    def _create_system_prompt(self) -> str:
        """Создает системный промпт для AI"""
        return """Ты — AI Analyst для DeepCalm, системы автоматизации performance маркетинга массажных салонов.

ТВОЯ РОЛЬ:
- Анализируешь эффективность рекламных кампаний
- Даешь конкретные рекомендации по оптимизации
- Фокусируешься на ROI и конверсионных метриках

КЛЮЧЕВЫЕ МЕТРИКИ:
- CAC (Customer Acquisition Cost) — стоимость привлечения клиента
- ROAS (Return on Ad Spend) — возврат на рекламные расходы
- CR (Conversion Rate) — процент конверсии лидов в клиентов
- LTV — lifetime value клиента массажного салона

КОНТЕКСТ МАССАЖНОГО БИЗНЕСА:
- Средний чек: 3000-5000 рублей
- Повторные визиты: 40-60% клиентов
- Сезонность: пики в праздники и стрессовые периоды
- Целевая аудитория: преимущественно женщины 25-45 лет

ФОРМАТ ОТВЕТА:
1. КРАТКИЙ ВЫВОД (1-2 предложения)
2. АНАЛИЗ МЕТРИК (CAC, ROAS, CR)
3. ПРОБЛЕМЫ (если есть)
4. РЕКОМЕНДАЦИИ (конкретные действия)
5. ПРОГНОЗ (ожидаемые результаты)

Будь конкретным, используй цифры, давай actionable советы."""

    def _create_user_prompt(self, campaign_data: Dict[str, Any], user_question: Optional[str] = None) -> str:
        """Создает пользовательский промпт с данными кампании"""
        prompt = f"""АНАЛИЗ КАМПАНИИ: {campaign_data['campaign']['title']}

ДАННЫЕ КАМПАНИИ:
- SKU: {campaign_data['campaign']['sku']}
- Статус: {campaign_data['campaign']['status']}
- Бюджет: {campaign_data['campaign']['budget_rub']:,} руб
- Потрачено: {campaign_data['metrics']['total_spend']:,} руб
- Цель CAC: {campaign_data['targets']['target_cac']:,} руб
- Цель ROAS: {campaign_data['targets']['target_roas']}

ТЕКУЩИЕ МЕТРИКИ (30 дней):
- Лиды: {campaign_data['metrics']['total_leads']}
- Конверсии: {campaign_data['metrics']['total_conversions']}
- Конверсия: {campaign_data['metrics']['conversion_rate']}%
- Выручка: {campaign_data['metrics']['total_revenue']:,} руб
- Факт ROAS: {campaign_data['metrics']['roas']}
- Факт CAC: {campaign_data['metrics']['cac']:,} руб

КРЕАТИВЫ:
"""

        for creative in campaign_data['creatives']:
            prompt += f"- {creative['variant']}: {creative['title']} (статус: {creative['status']})\n"

        if user_question:
            prompt += f"\nВОПРОС ОТ ПОЛЬЗОВАТЕЛЯ: {user_question}"

        prompt += "\nДай полный анализ и рекомендации по оптимизации этой кампании."

        return prompt

    def _extract_recommendations(self, analysis_text: str) -> List[str]:
        """Извлекает рекомендации из анализа (простая версия)"""
        # Простое извлечение - ищем секцию с рекомендациями
        lines = analysis_text.split('\n')
        recommendations = []
        in_recommendations = False

        for line in lines:
            line = line.strip()
            if 'рекомендаци' in line.lower():
                in_recommendations = True
                continue
            elif 'прогноз' in line.lower() or 'заключение' in line.lower():
                in_recommendations = False
            elif in_recommendations and line and (line.startswith('-') or line.startswith('•')):
                recommendations.append(line[1:].strip())

        return recommendations

    def chat_with_analyst(self, message: str, campaign_id: Optional[int] = None) -> str:
        """Чат с AI аналитиком"""
        try:
            # Базовый промпт для чата
            system_prompt = """Ты — AI Analyst для DeepCalm. Отвечай на вопросы о performance маркетинге массажных салонов.

Будь конкретным, используй экспертизу в digital маркетинге, давай практические советы.
Если вопрос не связан с маркетингом — вежливо перенаправь на маркетинговую тему."""

            user_prompt = message

            # Если указана кампания, добавляем её данные
            if campaign_id:
                campaign_data = self.get_campaign_data(campaign_id)
                user_prompt = f"КОНТЕКСТ: Кампания '{campaign_data['campaign']['title']}' с метриками: ROAS {campaign_data['metrics']['roas']}, CAC {campaign_data['metrics']['cac']} руб.\n\nВОПРОС: {message}"

            response = self.openai_client.chat.completions.create(
                model=self._settings.get("ai_model", "gpt-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self._settings.get("ai_temperature", 0.3),
                max_tokens=self._settings.get("ai_max_tokens", 1000)
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error("ai_chat_failed", message=message, error=str(e))
            raise
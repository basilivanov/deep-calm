"""
DeepCalm — Creative Generator Service

Mock-сервис генерации креативов для MVP.
Согласно DEEP-CALM-MVP-BLUEPRINT.md, для MVP используем placeholder текст.
Реальная LLM генерация — Фаза 3.
"""
from typing import List, Dict
import structlog
from uuid import UUID

from app.models.campaign import Campaign

logger = structlog.get_logger(__name__)


class CreativeGenerator:
    """
    Генератор креативов для рекламных кампаний.

    MVP: Использует шаблоны с подстановкой SKU.
    Phase 3: Реальная генерация через GPT-4/Claude.
    """

    # Шаблоны заголовков по SKU
    TITLE_TEMPLATES = {
        "RELAX-60": [
            "Релакс массаж 60 минут — глубокое расслабление",
            "Час тишины и спокойствия — релакс массаж",
            "Классический массаж 60 минут — снимите напряжение"
        ],
        "RELAX-90": [
            "Релакс массаж 90 минут — полное расслабление",
            "Полтора часа для себя — релакс массаж",
            "Максимальное расслабление за 90 минут"
        ],
        "DEEP-90": [
            "Глубокий массаж 90 минут — проработка мышц",
            "Глубокая техника массажа — 90 минут",
            "Интенсивный массаж для спортсменов"
        ],
        "THERAPY-60": [
            "Терапевтический массаж 60 минут",
            "Массаж для здоровья спины и шеи",
            "Лечебный массаж — 60 минут"
        ]
    }

    # Шаблоны текстов
    BODY_TEMPLATES = {
        "RELAX-60": [
            "Глубокое расслабление. Без боли. Тишина на час. Опытный мастер. Чистый кабинет в центре.",
            "Мягкие техники. Комфортная атмосфера. Час только для вас. Запись онлайн.",
            "Снимите стресс после рабочего дня. Авторские техники. Индивидуальный подход."
        ],
        "RELAX-90": [
            "Полтора часа глубокого расслабления. Мягкие техники. Тихая атмосфера. Опытный специалист.",
            "Максимальный релакс за 90 минут. Без боли и дискомфорта. Чистый кабинет.",
            "Забудьте о стрессе. Полное расслабление тела и разума. Комфортные условия."
        ],
        "DEEP-90": [
            "Глубокая проработка мышц. Для спортсменов и активных людей. 90 минут интенсива.",
            "Снимите мышечное напряжение. Глубокие техники. Восстановление после тренировок.",
            "Проработка триггерных точек. Эффективно и профессионально. 90 минут."
        ],
        "THERAPY-60": [
            "Терапевтический массаж для здоровья спины. Опытный специалист. 60 минут заботы.",
            "Лечебные техники для шеи и спины. Облегчение боли. Профессиональный подход.",
            "Восстановление после сидячей работы. Терапевтический массаж. Эффективно."
        ]
    }

    CTA_OPTIONS = [
        "Записаться онлайн",
        "Узнать свободное время",
        "Забронировать сеанс"
    ]

    def __init__(self):
        """Инициализация генератора"""
        pass

    def generate_creatives(
        self,
        campaign: Campaign,
        count: int = 3,
        temperature: float = 0.8
    ) -> List[Dict]:
        """
        Генерирует креативы для кампании.

        Args:
            campaign: Campaign объект
            count: Количество вариантов (1-5)
            temperature: Креативность (не используется в MVP)

        Returns:
            Список словарей с креативами

        Examples:
            >>> generator = CreativeGenerator()
            >>> creatives = generator.generate_creatives(campaign, count=3)
            >>> len(creatives)
            3
        """
        logger.info(
            "creative_generation_started",
            campaign_id=str(campaign.id),
            sku=campaign.sku,
            count=count
        )

        sku = campaign.sku
        variants = ["A", "B", "C", "D", "E"][:count]

        # Получаем шаблоны для SKU
        titles = self.TITLE_TEMPLATES.get(sku, [
            f"{sku} — профессиональный массаж",
            f"Массаж {sku} — опытный мастер",
            f"{sku} — запись онлайн"
        ])
        bodies = self.BODY_TEMPLATES.get(sku, [
            f"Профессиональный массаж {sku}. Опытный мастер. Чистый кабинет.",
            f"Качественный массаж {sku}. Комфортная атмосфера. Запись онлайн.",
            f"Авторские техники {sku}. Индивидуальный подход. Центр города."
        ])

        creatives = []
        for i, variant in enumerate(variants):
            creative_data = {
                "variant": variant,
                "title": titles[i % len(titles)],
                "body": bodies[i % len(bodies)],
                "cta": self.CTA_OPTIONS[i % len(self.CTA_OPTIONS)],
                "image_url": None,  # TODO: Phase 3 - генерация изображений
                "generated_by": "llm",
                "moderation_status": "pending"
            }
            creatives.append(creative_data)

        logger.info(
            "creatives_generated",
            campaign_id=str(campaign.id),
            count=len(creatives),
            status="success"
        )

        return creatives

    def validate_creative(self, creative_data: Dict) -> bool:
        """
        Валидация креатива на соответствие brandbook.

        Args:
            creative_data: Словарь с данными креатива

        Returns:
            True если валидация прошла

        TODO: Phase 1.5 - реальная проверка через brandbook/creative_rules.md
        """
        # Проверка стоп-слов (из STANDARDS.yml и brandbook)
        stop_words = ["эротический", "интимный", "тантра", "yoni"]
        text = (creative_data.get("title", "") + " " + creative_data.get("body", "")).lower()

        for word in stop_words:
            if word in text:
                logger.warning(
                    "creative_validation_failed",
                    reason=f"stop_word_found: {word}"
                )
                return False

        return True

"""
DeepCalm — Structured Logging

structlog с JSON форматом и PII-маскированием.
Соответствует cortex/DEEP-CALM-INFRASTRUCTURE.md и STANDARDS.yml
"""
import logging
import re
import structlog
from structlog.processors import JSONRenderer
from typing import Any, Dict

from app.core.config import settings


def mask_pii(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """
    Маскирует PII (Personally Identifiable Information) в логах.

    Маскирует:
    - Телефоны: +79991234567 → +7999***4567
    - Email: vasya@example.com → v***a@example.com

    Args:
        logger: Logger instance
        method_name: Имя метода логирования
        event_dict: Словарь с данными события

    Returns:
        Модифицированный event_dict с замаскированными PII

    Examples:
        >>> logger.info("lead_created", phone="+79991234567")
        >>> # Вывод: {"phone": "+7999***4567", ...}
    """
    for key, value in event_dict.items():
        if isinstance(value, str):
            # Телефоны: +79991234567 → +7999***4567
            value = re.sub(r'(\+7\d{3})\d{3}(\d{4})', r'\1***\2', value)

            # Email: vasya@example.com → v***a@example.com
            value = re.sub(r'(\w)\w+(\w)@', r'\1***\2@', value)

            event_dict[key] = value

    return event_dict


def setup_logging() -> None:
    """
    Настраивает structlog для production-ready логирования.

    Процессоры:
    1. merge_contextvars — correlation_id из контекста
    2. filter_by_level — фильтрация по уровню
    3. add_logger_name — имя логгера
    4. add_log_level — уровень лога
    5. TimeStamper — ISO timestamp
    6. StackInfoRenderer — stack traces
    7. format_exc_info — форматирование исключений
    8. mask_pii — маскирование PII
    9. JSONRenderer — JSON output

    Согласно STANDARDS.yml:
    - json: true
    - fields: [ts, level, app, svc, env, req_id, route, status, msg]
    - pii_mask: true
    """
    log_level = logging.DEBUG if settings.app_debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            mask_pii,
            JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Настройка stdlib logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=[logging.StreamHandler()]
    )


# Инициализация при импорте
setup_logging()

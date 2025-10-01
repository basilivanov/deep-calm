"""
Seed data для базы данных DeepCalm

Запускается один раз при инициализации системы для заполнения справочников.
"""
import structlog
from sqlalchemy.orm import Session

from app.models.channel import Channel

logger = structlog.get_logger(__name__)


def seed_channels(db: Session) -> None:
    """
    Заполняет таблицу channels начальными данными.

    Args:
        db: SQLAlchemy session
    """
    # Проверяем, есть ли уже данные
    existing_count = db.query(Channel).count()
    if existing_count > 0:
        logger.info("channels_already_seeded", count=existing_count)
        return

    channels_data = [
        {
            "code": "vk",
            "name": "VK Ads",
            "api_endpoint": "https://ads.vk.com/api/v2/",
            "enabled": True
        },
        {
            "code": "direct",
            "name": "Яндекс.Директ",
            "api_endpoint": "https://api.direct.yandex.com/json/v5/",
            "enabled": True
        },
        {
            "code": "avito",
            "name": "Avito",
            "api_endpoint": "https://api.avito.ru/v2/",
            "enabled": True
        }
    ]

    for channel_data in channels_data:
        channel = Channel(**channel_data)
        db.add(channel)
        logger.info(
            "channel_seeded",
            code=channel_data["code"],
            name=channel_data["name"]
        )

    db.commit()
    logger.info("channels_seed_completed", total=len(channels_data))


def seed_all(db: Session) -> None:
    """
    Запускает все seed функции.

    Args:
        db: SQLAlchemy session
    """
    logger.info("seed_all_started")
    seed_channels(db)
    logger.info("seed_all_completed")

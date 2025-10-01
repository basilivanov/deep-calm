from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Добавляем путь к app в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Импортируем Base и все модели
from app.models import Base  # noqa
# Импортируем все модели для автогенерации
from app.models.channel import Channel  # noqa
from app.models.campaign import Campaign  # noqa
from app.models.creative import Creative  # noqa
from app.models.placement import Placement  # noqa
from app.models.lead import Lead  # noqa
from app.models.conversion import Conversion  # noqa

# Конфиг Alembic
config = context.config

# Берём DATABASE_URL из переменной окружения, если есть
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Настройка логгера
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata для auto-generate миграций
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
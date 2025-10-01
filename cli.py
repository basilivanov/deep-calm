#!/usr/bin/env python3
"""
CLI команды для DeepCalm

Использование:
    python cli.py seed  # Заполнить справочники
"""
import sys
import structlog
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.logging import setup_logging
from app.core.seed import seed_all

# Настройка логирования
setup_logging()
logger = structlog.get_logger(__name__)


def run_seed():
    """Запускает seed для заполнения справочников"""
    logger.info("cli_seed_started")
    db: Session = SessionLocal()
    try:
        seed_all(db)
        logger.info("cli_seed_completed")
    except Exception as e:
        logger.error("cli_seed_failed", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        db.close()


def main():
    """Основная функция CLI"""
    if len(sys.argv) < 2:
        print("Usage: python cli.py <command>")
        print("\nCommands:")
        print("  seed    - Заполнить справочники начальными данными")
        sys.exit(1)

    command = sys.argv[1]

    if command == "seed":
        run_seed()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

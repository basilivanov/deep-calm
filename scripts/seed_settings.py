#!/usr/bin/env python3
"""
DeepCalm — Seed Initial Settings

Создает начальные настройки для AI Analyst и других компонентов.
Работает напрямую с PostgreSQL.
"""
import psycopg2
import sys
from typing import List, Dict

# Начальные настройки согласно DEEP-CALM-MVP-BLUEPRINT.md
INITIAL_SETTINGS = [
    # Финансовые показатели
    {
        "key": "target_monthly_revenue_rub",
        "value": "100000",
        "value_type": "int",
        "category": "financial",
        "description": "Целевая месячная выручка (спидометр в админке)",
        "updated_by": "system"
    },
    {
        "key": "target_cac_rub",
        "value": "500",
        "value_type": "int",
        "category": "financial",
        "description": "Целевой CAC (можно увеличить если не укладываемся)",
        "updated_by": "system"
    },
    {
        "key": "target_roas",
        "value": "5.0",
        "value_type": "float",
        "category": "financial",
        "description": "Целевой ROAS (Return on Ad Spend): выручка / расходы",
        "updated_by": "system"
    },
    {
        "key": "max_daily_spend_per_channel_rub",
        "value": "2000",
        "value_type": "int",
        "category": "financial",
        "description": "Максимальный расход на канал в день",
        "updated_by": "system"
    },

    # Цены на услуги (SKU)
    {
        "key": "sku_relax60_price_rub",
        "value": "3500",
        "value_type": "int",
        "category": "pricing",
        "description": "Цена SKU RELAX-60",
        "updated_by": "system"
    },
    {
        "key": "sku_relax90_price_rub",
        "value": "4800",
        "value_type": "int",
        "category": "pricing",
        "description": "Цена SKU RELAX-90",
        "updated_by": "system"
    },
    {
        "key": "sku_deep90_price_rub",
        "value": "4200",
        "value_type": "int",
        "category": "pricing",
        "description": "Цена SKU DEEP-90",
        "updated_by": "system"
    },
    {
        "key": "sku_therapy60_price_rub",
        "value": "4200",
        "value_type": "int",
        "category": "pricing",
        "description": "Цена SKU THERAPY-60",
        "updated_by": "system"
    },

    # Операционные лимиты
    {
        "key": "max_monthly_clients",
        "value": "80",
        "value_type": "int",
        "category": "operational",
        "description": "Максимум клиентов в месяц (ограничение при переборе)",
        "updated_by": "system"
    },
    {
        "key": "workload_capacity_hours_per_month",
        "value": "160",
        "value_type": "int",
        "category": "operational",
        "description": "Пропускная способность (часов/месяц)",
        "updated_by": "system"
    },

    # Алерты и пороги
    {
        "key": "alert_cac_threshold_rub",
        "value": "700",
        "value_type": "int",
        "category": "alerts",
        "description": "Отправить алерт если CAC превысит порог",
        "updated_by": "system"
    },
    {
        "key": "alert_roas_threshold",
        "value": "3.0",
        "value_type": "float",
        "category": "alerts",
        "description": "Алерт при ROAS < 3.0 (окупаемость низкая)",
        "updated_by": "system"
    },
    {
        "key": "pause_campaign_if_cac_exceeds_rub",
        "value": "1000",
        "value_type": "int",
        "category": "alerts",
        "description": "Автопауза кампании при CAC выше",
        "updated_by": "system"
    },

    # AI поведение
    {
        "key": "chatbot_confidence_threshold",
        "value": "0.70",
        "value_type": "float",
        "category": "ai",
        "description": "Порог уверенности чатбота (эскалация при < 70%)",
        "updated_by": "system"
    },
    {
        "key": "creative_generation_temp",
        "value": "0.8",
        "value_type": "float",
        "category": "ai",
        "description": "Temperature для GPT-4 при генерации креативов",
        "updated_by": "system"
    },
    {
        "key": "analyst_report_schedule_cron",
        "value": "0 9 * * MON",
        "value_type": "string",
        "category": "ai",
        "description": "Расписание отчётов AI Аналитика (каждый понедельник 9:00)",
        "updated_by": "system"
    }
]


def create_setting(cursor, setting: Dict) -> bool:
    """Создает настройку в БД"""
    try:
        # Проверяем существует ли настройка
        cursor.execute("SELECT key FROM settings WHERE key = %s", (setting['key'],))
        if cursor.fetchone():
            print(f"⚠️  Уже существует: {setting['key']}")
            return True

        # Создаем настройку
        cursor.execute("""
            INSERT INTO settings (key, value, value_type, category, description, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            setting['key'],
            setting['value'],
            setting['value_type'],
            setting['category'],
            setting['description'],
            setting['updated_by']
        ))
        print(f"✅ Создана: {setting['key']}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании {setting['key']}: {e}")
        return False


def connect_to_db():
    """Подключается к PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="dc_dev",
            user="dc",
            password="dcpass"
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None


def main():
    """Основная функция"""
    print("🚀 DeepCalm Settings Seeder")
    print("=" * 40)

    # Подключаемся к БД
    conn = connect_to_db()
    if not conn:
        sys.exit(1)

    try:
        cursor = conn.cursor()
        print(f"📋 Создаем {len(INITIAL_SETTINGS)} начальных настроек...")

        success_count = 0
        for setting in INITIAL_SETTINGS:
            if create_setting(cursor, setting):
                success_count += 1

        # Коммитим изменения
        conn.commit()

        print("=" * 40)
        print(f"✅ Успешно: {success_count}/{len(INITIAL_SETTINGS)}")

        if success_count < len(INITIAL_SETTINGS):
            print("⚠️  Некоторые настройки не созданы. Проверьте логи выше.")
            sys.exit(1)
        else:
            print("🎉 Все настройки созданы успешно!")

    except Exception as e:
        print(f"❌ Ошибка при работе с БД: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
DeepCalm — Seed Initial Settings

Создает начальные настройки для AI Analyst и других компонентов.
"""
import requests
import sys
from typing import List, Dict

# Настройки API
API_BASE = "http://127.0.0.1:8000/api/v1"

# Начальные настройки для Phase 1.5
INITIAL_SETTINGS = [
    # AI Analyst настройки
    {
        "key": "openai_api_key",
        "value": "sk-your-openai-key-here",
        "value_type": "string",
        "category": "ai",
        "description": "OpenAI API ключ для GPT-4 анализа кампаний",
        "updated_by": "system"
    },
    {
        "key": "ai_model",
        "value": "gpt-4",
        "value_type": "string",
        "category": "ai",
        "description": "Модель OpenAI для анализа (gpt-4, gpt-3.5-turbo)",
        "updated_by": "system"
    },
    {
        "key": "ai_temperature",
        "value": "0.3",
        "value_type": "float",
        "category": "ai",
        "description": "Temperature для AI анализа (0.0-1.0, 0.3 = консервативно)",
        "updated_by": "system"
    },
    {
        "key": "ai_max_tokens",
        "value": "2000",
        "value_type": "int",
        "category": "ai",
        "description": "Максимум токенов для ответа AI Analyst",
        "updated_by": "system"
    },

    # Financial limits
    {
        "key": "max_campaign_budget",
        "value": "100000",
        "value_type": "int",
        "category": "financial",
        "description": "Максимальный бюджет кампании (рублей)",
        "updated_by": "system"
    },
    {
        "key": "min_roas_threshold",
        "value": "2.0",
        "value_type": "float",
        "category": "financial",
        "description": "Минимальный ROAS для продолжения кампании",
        "updated_by": "system"
    },
    {
        "key": "alert_cac_threshold",
        "value": "3000",
        "value_type": "int",
        "category": "alerts",
        "description": "CAC выше этого значения вызывает алерт (рублей)",
        "updated_by": "system"
    },

    # Operational settings
    {
        "key": "reports_enabled",
        "value": "true",
        "value_type": "bool",
        "category": "operational",
        "description": "Включены ли еженедельные отчеты",
        "updated_by": "system"
    },
    {
        "key": "reports_email",
        "value": "admin@deepcalm.local",
        "value_type": "string",
        "category": "operational",
        "description": "Email для отправки отчетов",
        "updated_by": "system"
    },
    {
        "key": "analysis_frequency_hours",
        "value": "24",
        "value_type": "int",
        "category": "operational",
        "description": "Частота автоматического анализа кампаний (часов)",
        "updated_by": "system"
    },

    # Pricing strategy
    {
        "key": "default_target_cac",
        "value": "2500",
        "value_type": "int",
        "category": "pricing",
        "description": "Целевой CAC по умолчанию (рублей)",
        "updated_by": "system"
    },
    {
        "key": "default_target_roas",
        "value": "3.0",
        "value_type": "float",
        "category": "pricing",
        "description": "Целевой ROAS по умолчанию",
        "updated_by": "system"
    }
]


def create_setting(setting: Dict) -> bool:
    """Создает настройку через API"""
    try:
        response = requests.post(f"{API_BASE}/settings", json=setting, timeout=10)
        if response.status_code == 201:
            print(f"✅ Создана: {setting['key']}")
            return True
        elif response.status_code == 409:
            print(f"⚠️  Уже существует: {setting['key']}")
            return True
        else:
            print(f"❌ Ошибка {response.status_code}: {setting['key']} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Сетевая ошибка для {setting['key']}: {e}")
        return False


def check_api_health() -> bool:
    """Проверяет доступность API"""
    try:
        response = requests.get(f"http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Основная функция"""
    print("🚀 DeepCalm Settings Seeder")
    print("=" * 40)

    # Проверяем API
    if not check_api_health():
        print("❌ API недоступен. Убедитесь что API запущен на http://127.0.0.1:8000")
        sys.exit(1)

    print(f"📋 Создаем {len(INITIAL_SETTINGS)} начальных настроек...")

    success_count = 0
    for setting in INITIAL_SETTINGS:
        if create_setting(setting):
            success_count += 1

    print("=" * 40)
    print(f"✅ Успешно: {success_count}/{len(INITIAL_SETTINGS)}")

    if success_count < len(INITIAL_SETTINGS):
        print("⚠️  Некоторые настройки не созданы. Проверьте логи выше.")
        sys.exit(1)
    else:
        print("🎉 Все настройки созданы успешно!")


if __name__ == "__main__":
    main()
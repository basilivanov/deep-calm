#!/usr/bin/env python3
"""Тестируем подключение к песочнице Яндекс.Директ с текущим токеном."""

import json
import os
import sys
from pathlib import Path

import urllib.request
import urllib.parse
import urllib.error

# Загружаем токен из env файла
ROOT_DIR = Path(__file__).resolve().parent.parent
DEV_ENV_PATH = ROOT_DIR / "dev" / "env"

def load_env_vars():
    """Загружает переменные из dev/env файла."""
    env_vars = {}
    if DEV_ENV_PATH.exists():
        for line in DEV_ENV_PATH.read_text().splitlines():
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def test_yandex_direct_connection():
    """Тестирует подключение к Яндекс.Директ API."""
    env_vars = load_env_vars()

    token = env_vars.get('DC_YANDEX_DIRECT_TOKEN')
    login = env_vars.get('DC_YANDEX_DIRECT_LOGIN')

    if not token:
        print("❌ Токен не найден в dev/env")
        return False

    print(f"🔑 Токен: {token[:10]}...")
    if login:
        print(f"👤 Логин: {login}")

    # Тестируем подключение к песочнице
    sandbox_url = "https://api-sandbox.direct.yandex.com/json/v5/campaigns"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "DeepCalm/1.0",
    }

    if login:
        headers["Client-Login"] = login

    # Простой запрос на получение кампаний
    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State"]
        }
    }

    print("\n🔄 Тестируем подключение к песочнице...")
    print(f"URL: {sandbox_url}")
    print(f"Headers: {json.dumps({k: v[:10] + '...' if k == 'Authorization' else v for k, v in headers.items()}, indent=2)}")

    try:
        # Создаём запрос
        request_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            sandbox_url,
            data=request_data,
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=15.0) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')

        print(f"\n📊 Статус ответа: {status_code}")

        if status_code == 200:
            data = json.loads(response_data)
            if "result" in data:
                campaigns = data["result"].get("Campaigns", [])
                print(f"✅ Подключение успешно! Найдено кампаний: {len(campaigns)}")
                for campaign in campaigns[:3]:  # Показываем первые 3
                    print(f"  - {campaign.get('Name', 'Без названия')} (ID: {campaign.get('Id')})")
                return True
            elif "error" in data:
                error = data["error"]
                print(f"❌ Ошибка API: {error.get('error_string', 'Неизвестная ошибка')}")
                print(f"   Код: {error.get('error_code')}")
                print(f"   Детали: {error.get('error_detail', 'Нет деталей')}")
                return False

        print(f"\n📄 Тело ответа:")
        try:
            print(json.dumps(json.loads(response_data), indent=2, ensure_ascii=False))
        except:
            print(response_data)

    except urllib.error.HTTPError as e:
        status_code = e.code
        response_data = e.read().decode('utf-8')

        print(f"\n📊 Статус ответа: {status_code}")

        if status_code == 401:
            print("❌ Ошибка 401: Неавторизован")
            print("   Возможные причины:")
            print("   - Токен недействителен или истёк")
            print("   - Неправильный формат заголовка Authorization")
            print("   - Нет доступа к песочнице")
        elif status_code == 403:
            print("❌ Ошибка 403: Доступ запрещён")
            print("   Возможные причины:")
            print("   - Нет доступа к песочнице Яндекс.Директ")
            print("   - Приложение не одобрено для использования API")
        else:
            print(f"❌ Неожиданный статус: {status_code}")

        print(f"\n📄 Тело ответа:")
        try:
            print(json.dumps(json.loads(response_data), indent=2, ensure_ascii=False))
        except:
            print(response_data)

    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

    return False

def test_oauth_token_validity():
    """Проверяет валидность OAuth токена через Yandex ID API."""
    env_vars = load_env_vars()
    token = env_vars.get('DC_YANDEX_DIRECT_TOKEN')

    if not token:
        return False

    print("\n🔍 Проверяем валидность OAuth токена...")

    try:
        req = urllib.request.Request(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {token}"}
        )

        with urllib.request.urlopen(req, timeout=10.0) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')

        if status_code == 200:
            data = json.loads(response_data)
            print(f"✅ Токен валиден для пользователя: {data.get('login', 'Неизвестно')}")
            return True
        else:
            print(f"❌ Токен не валиден (статус: {status_code})")
            return False

    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")
        return False

if __name__ == "__main__":
    print("=== Тестирование подключения к Яндекс.Директ ===\n")

    # Проверяем валидность токена
    token_valid = test_oauth_token_validity()

    # Тестируем API
    api_works = test_yandex_direct_connection()

    print("\n" + "="*50)
    if token_valid and api_works:
        print("🎉 Всё работает!")
        sys.exit(0)
    elif token_valid and not api_works:
        print("🔧 Токен валиден, но API недоступен")
        print("\nВозможные решения:")
        print("1. Запросить доступ к песочнице в интерфейсе Директа")
        print("2. Подождать одобрения заявки (может занять до 24 часов)")
        print("3. Проверить правильность Client-Login")
        sys.exit(1)
    else:
        print("❌ Проблемы с токеном или подключением")
        print("\nРекомендации:")
        print("1. Получить новый токен через scripts/setup_yandex_direct_token.py")
        print("2. Проверить настройки приложения на oauth.yandex.ru")
        sys.exit(1)
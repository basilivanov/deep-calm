#!/usr/bin/env python3
"""Детальная диагностика API Яндекс.Директ."""

import json
import sys
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

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

def debug_get_campaigns():
    """Детальная диагностика запроса campaigns/get."""
    env_vars = load_env_vars()
    token = env_vars.get('DC_YANDEX_DIRECT_TOKEN')
    login = env_vars.get('DC_YANDEX_DIRECT_LOGIN')

    if not token:
        print("❌ Токен не найден в dev/env")
        return False

    print(f"🔑 Токен: {token[:15]}...")
    print(f"👤 Логин: '{login}' (длина: {len(login) if login else 0})")

    # Убираем login если пустой
    if login and not login.strip():
        login = None
        print("🔄 Убираем пустой логин (роль 'Клиент')")

    sandbox_url = "https://api-sandbox.direct.yandex.com/json/v5/campaigns"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "DeepCalm/1.0",
    }

    if login:
        headers["Client-Login"] = login
        print(f"🏢 Используем Client-Login: {login}")
    else:
        print("👤 Работаем без Client-Login (роль 'Клиент')")

    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State", "Type"]
        }
    }

    print(f"\\n📡 Отправляем запрос:")
    print(f"URL: {sandbox_url}")
    print(f"Method: POST")
    print(f"Headers: {json.dumps({k: (v[:15] + '...' if k == 'Authorization' else v) for k, v in headers.items()}, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
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

        print(f"\\n📊 Ответ:")
        print(f"Статус: {status_code}")

        try:
            data = json.loads(response_data)
            print(f"JSON структура:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if "result" in data:
                campaigns = data["result"].get("Campaigns", [])
                print(f"\\n✅ Успешно получено кампаний: {len(campaigns)}")
                return True
            elif "error" in data:
                error = data["error"]
                print(f"\\n❌ Ошибка API:")
                print(f"   Код: {error.get('error_code')}")
                print(f"   Строка: {error.get('error_string')}")
                print(f"   Детали: {error.get('error_detail')}")
                print(f"   Описание: {error.get('request_id', 'N/A')}")
                return False
            else:
                print(f"\\n⚠️ Неожиданная структура ответа")
                return False

        except json.JSONDecodeError:
            print(f"❌ Не удалось разобрать JSON:")
            print(response_data)
            return False

    except urllib.error.HTTPError as e:
        status_code = e.code
        response_data = e.read().decode('utf-8')

        print(f"\\n❌ HTTP ошибка {status_code}")
        print(f"Тело ответа:")
        try:
            error_data = json.loads(response_data)
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except:
            print(response_data)
        return False

    except Exception as e:
        print(f"\\n❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("=== Детальная диагностика API Яндекс.Директ ===\\n")
    debug_get_campaigns()
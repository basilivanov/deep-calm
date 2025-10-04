#!/usr/bin/env python3
"""Исправляем проблему с Client-Login для песочницы Яндекс.Директ."""

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

def update_env_file(path: Path, updates: dict) -> None:
    """Обновляет env файл."""
    lines = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    updated_lines = []
    processed_keys = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            updated_lines.append(line)
            continue

        key, _ = line.split("=", 1)
        key = key.strip()
        if key in updates:
            updated_lines.append(f"{key}={updates[key]}")
            processed_keys.add(key)
        else:
            updated_lines.append(line)

    for key, value in updates.items():
        if key not in processed_keys:
            if updated_lines and updated_lines[-1].strip():
                updated_lines.append("")
            updated_lines.append(f"{key}={value}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\\n".join(updated_lines) + "\\n", encoding="utf-8")

def test_api_without_client_login(token):
    """Тестирует API без Client-Login (для прямых клиентов)."""
    print("\\n🔄 Тестируем без Client-Login (роль 'Клиент')...")

    sandbox_url = "https://api-sandbox.direct.yandex.com/json/v5/campaigns"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "DeepCalm/1.0",
    }

    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State"]
        }
    }

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

        if status_code == 200:
            data = json.loads(response_data)
            if "result" in data:
                campaigns = data["result"].get("Campaigns", [])
                print(f"✅ Подключение успешно! Найдено кампаний: {len(campaigns)}")
                for campaign in campaigns[:3]:
                    print(f"  - {campaign.get('Name', 'Без названия')} (ID: {campaign.get('Id')})")

                # Убираем Client-Login из env
                print("\\n📝 Обновляем dev/env (убираем Client-Login)...")
                updates = {
                    "DC_YANDEX_DIRECT_LOGIN": "",
                    "YANDEX_DIRECT_LOGIN": ""
                }
                update_env_file(DEV_ENV_PATH, updates)
                print("✅ Client-Login убран из конфигурации")
                return True
            elif "error" in data:
                error = data["error"]
                print(f"❌ Ошибка API: {error.get('error_string', 'Неизвестная ошибка')}")
                print(f"   Код: {error.get('error_code')}")
                return False

    except urllib.error.HTTPError as e:
        status_code = e.code
        response_data = e.read().decode('utf-8')
        print(f"❌ HTTP ошибка {status_code}")
        try:
            error_data = json.loads(response_data)
            print(f"   Детали: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   Ответ: {response_data}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

    return False

def get_agency_clients(token):
    """Получает список клиентов агентства."""
    print("\\n🔄 Получаем список клиентов агентства...")

    clients_url = "https://api-sandbox.direct.yandex.com/json/v5/agencyclients"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "DeepCalm/1.0",
    }

    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Login", "ClientInfo"]
        }
    }

    try:
        request_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            clients_url,
            data=request_data,
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=15.0) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')

        if status_code == 200:
            data = json.loads(response_data)
            if "result" in data:
                clients = data["result"].get("Clients", [])
                print(f"✅ Найдено клиентов: {len(clients)}")

                if clients:
                    first_client = clients[0]
                    login = first_client.get("Login")
                    print(f"\\n📋 Доступные клиенты:")
                    for client in clients:
                        print(f"  - Логин: {client.get('Login')}")

                    if login:
                        print(f"\\n📝 Обновляем dev/env (используем первого клиента: {login})...")
                        updates = {
                            "DC_YANDEX_DIRECT_LOGIN": login,
                            "YANDEX_DIRECT_LOGIN": login
                        }
                        update_env_file(DEV_ENV_PATH, updates)
                        print(f"✅ Client-Login установлен: {login}")
                        return login
                else:
                    print("⚠️ Нет доступных клиентов")
                    return None
            elif "error" in data:
                error = data["error"]
                print(f"❌ Ошибка API: {error.get('error_string', 'Неизвестная ошибка')}")
                print(f"   Код: {error.get('error_code')}")
                return None

    except urllib.error.HTTPError as e:
        status_code = e.code
        response_data = e.read().decode('utf-8')
        print(f"❌ HTTP ошибка {status_code}")
        if status_code == 403:
            print("   Возможно, у вас роль 'Клиент', а не 'Агентство'")
        try:
            error_data = json.loads(response_data)
            print(f"   Детали: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   Ответ: {response_data}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

    return None

def test_with_client_login(token, login):
    """Тестирует API с указанным Client-Login."""
    print(f"\\n🔄 Тестируем с Client-Login: {login}...")

    sandbox_url = "https://api-sandbox.direct.yandex.com/json/v5/campaigns"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "DeepCalm/1.0",
        "Client-Login": login
    }

    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State"]
        }
    }

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

        if status_code == 200:
            data = json.loads(response_data)
            if "result" in data:
                campaigns = data["result"].get("Campaigns", [])
                print(f"✅ Подключение успешно! Найдено кампаний: {len(campaigns)}")
                for campaign in campaigns[:3]:
                    print(f"  - {campaign.get('Name', 'Без названия')} (ID: {campaign.get('Id')})")
                return True
            elif "error" in data:
                error = data["error"]
                print(f"❌ Ошибка API: {error.get('error_string', 'Неизвестная ошибка')}")
                print(f"   Код: {error.get('error_code')}")
                return False

    except urllib.error.HTTPError as e:
        status_code = e.code
        response_data = e.read().decode('utf-8')
        print(f"❌ HTTP ошибка {status_code}")
        try:
            error_data = json.loads(response_data)
            print(f"   Детали: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   Ответ: {response_data}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

    return False

def main():
    print("=== Исправление Client-Login для песочницы Яндекс.Директ ===\\n")

    env_vars = load_env_vars()
    token = env_vars.get('DC_YANDEX_DIRECT_TOKEN')
    current_login = env_vars.get('DC_YANDEX_DIRECT_LOGIN')

    if not token:
        print("❌ Токен не найден в dev/env")
        return 1

    print(f"🔑 Токен: {token[:10]}...")
    if current_login:
        print(f"👤 Текущий логин: {current_login}")

    # Стратегия 1: Попробуем без Client-Login (роль "Клиент")
    if test_api_without_client_login(token):
        print("\\n🎉 Решение найдено: работаем без Client-Login (роль 'Клиент')")
        return 0

    # Стратегия 2: Попробуем получить список клиентов агентства
    agency_client_login = get_agency_clients(token)
    if agency_client_login:
        if test_with_client_login(token, agency_client_login):
            print(f"\\n🎉 Решение найдено: используем Client-Login {agency_client_login}")
            return 0

    print("\\n" + "="*50)
    print("❌ Не удалось подключиться к песочнице")
    print("\\nВозможные причины и решения:")
    print("1. 🔧 Песочница не активирована:")
    print("   - Откройте https://direct.yandex.ru")
    print("   - Перейдите в раздел API → Песочница")
    print("   - Нажмите 'Начать пользоваться Песочницей'")
    print("   - Выберите роль: 'Клиент' или 'Агентство'")
    print("\\n2. ⏰ Ожидание активации:")
    print("   - Активация может занять до 24 часов")
    print("   - Повторите попытку позже")
    print("\\n3. 🔑 Проблемы с токеном:")
    print("   - Получите новый токен через scripts/setup_yandex_direct_token.py")
    print("   - Проверьте настройки OAuth приложения")

    return 1

if __name__ == "__main__":
    sys.exit(main())
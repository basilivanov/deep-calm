#!/usr/bin/env python3
"""DeepCalm helper: configure Yandex.Direct OAuth token for dev stack.

Steps performed:
1. Ask the user for Client ID, Client Secret and login (Client-Login).
2. Provide the OAuth authorization URL so the user can grant access and copy the code.
3. Exchange the code for an access token via https://oauth.yandex.ru/token.
4. Store the token and login inside dev/env (and legacy variables without the DC_ prefix).
5. Print next steps (docker compose restart).

The script never prints the client secret after input, it is stored only in memory
for the token exchange request.
"""
from __future__ import annotations

import getpass
import json
import sys
from pathlib import Path
from typing import Dict
from urllib.parse import urlencode

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
DEV_ENV_PATH = ROOT_DIR / "dev" / "env"

AUTH_BASE_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"


def prompt(prompt_text: str, *, secret: bool = False, allow_empty: bool = False) -> str:
    while True:
        value = (getpass.getpass if secret else input)(prompt_text)
        value = value.strip()
        if value or allow_empty:
            return value
        print("Значение не может быть пустым. Повторите ввод.")


def build_auth_url(client_id: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "force_confirm": "yes",
    }
    return f"{AUTH_BASE_URL}?{urlencode(params)}"


def request_token(client_id: str, client_secret: str, auth_code: str) -> Dict[str, str]:
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Ошибка обмена кода на токен (HTTP {response.status_code}): {response.text}"
        )
    payload = response.json()
    if "access_token" not in payload:
        raise RuntimeError(f"В ответе нет access_token: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def update_env_file(path: Path, updates: Dict[str, str]) -> None:
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
    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def main() -> None:
    print("=== Настройка OAuth токена Яндекс.Директа (песочница) ===")
    client_id = prompt("Client ID (из https://oauth.yandex.ru): ")
    client_secret = prompt("Client Secret: ", secret=True)
    login = prompt(
        "Client-Login (логин рекламного кабинета; оставь пустым, если не требуется): ",
        allow_empty=True,
    )

    auth_url = build_auth_url(client_id)
    print("\n1) Открой ссылку в браузере и авторизуйся под нужным аккаунтом:")
    print(auth_url)
    print("2) Подтверди доступ и скопируй авторизационный код со страницы.")
    auth_code = prompt("Вставь полученный код сюда: ")

    print("\nОбмениваем код на OAuth токен...")
    try:
        token_response = request_token(client_id, client_secret, auth_code)
    except Exception as exc:  # noqa: BLE001
        print(f"Ошибка: {exc}")
        sys.exit(1)

    access_token = token_response["access_token"]
    print("Токен получен успешно.")

    updates = {
        "DC_YANDEX_DIRECT_TOKEN": access_token,
        "YANDEX_DIRECT_TOKEN": access_token,
    }
    if login:
        updates["DC_YANDEX_DIRECT_LOGIN"] = login
        updates["YANDEX_DIRECT_LOGIN"] = login
    update_env_file(DEV_ENV_PATH, updates)
    print(f"Файл {DEV_ENV_PATH} обновлён.")

    print(
        "\nДальше:")
    print("  1) Перезапусти API-контейнер: cd /opt/deep-calm/dev && docker compose up -d --force-recreate dc-api")
    print("  2) Проверь подключение: docker compose exec dc-api env | grep DC_YANDEX_DIRECT")
    print(
        "  3) Прогоняй health-скрипт или публикацию — теперь клиент должен работать в sandbox."  )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОтменено пользователем.")
        sys.exit(1)

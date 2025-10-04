"""
DeepCalm — Settings API Integration Tests

Тесты для CRUD операций Settings API.
Поддерживает типизированные настройки для AI Analyst.
"""
import pytest
from fastapi.testclient import TestClient

from app.models.setting import Setting


def test_get_settings_empty(client: TestClient):
    """
    GET /api/v1/settings — пустой список.

    Given: БД пустая
    When: GET /api/v1/settings
    Then: Возвращается пустой список с total=0
    """
    response = client.get("/api/v1/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["settings"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 50


def test_create_setting(client: TestClient):
    """
    POST /api/v1/settings — создание настройки.

    Given: Валидные данные настройки
    When: POST /api/v1/settings
    Then: Настройка создается с кодом 201
    """
    setting_data = {
        "key": "openai_api_key",
        "value": "sk-test123",
        "value_type": "string",
        "category": "ai",
        "description": "OpenAI API ключ для GPT-4",
        "updated_by": "admin"
    }

    response = client.post("/api/v1/settings", json=setting_data)

    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "openai_api_key"
    assert data["value"] == "sk-test123"
    assert data["value_type"] == "string"
    assert data["category"] == "ai"
    assert data["updated_at"] is not None


def test_create_setting_duplicate_key(client: TestClient):
    """
    POST /api/v1/settings — дублирование ключа.

    Given: Настройка с таким ключом уже существует
    When: POST /api/v1/settings с тем же ключом
    Then: Возвращается ошибка 409
    """
    setting_data = {
        "key": "test_key",
        "value": "value1",
        "value_type": "string",
        "category": "operational"
    }

    # Первое создание
    response1 = client.post("/api/v1/settings", json=setting_data)
    assert response1.status_code == 201

    # Повторное создание
    response2 = client.post("/api/v1/settings", json=setting_data)
    assert response2.status_code == 409
    assert "уже существует" in response2.json()["detail"]


def test_get_setting_by_key(client: TestClient):
    """
    GET /api/v1/settings/{key} — получение настройки по ключу.

    Given: Настройка существует
    When: GET /api/v1/settings/{key}
    Then: Возвращается настройка
    """
    # Создаем настройку
    setting_data = {
        "key": "max_budget",
        "value": "50000",
        "value_type": "int",
        "category": "financial"
    }
    client.post("/api/v1/settings", json=setting_data)

    # Получаем настройку
    response = client.get("/api/v1/settings/max_budget")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "max_budget"
    assert data["value"] == "50000"
    assert data["value_type"] == "int"


def test_get_setting_not_found(client: TestClient):
    """
    GET /api/v1/settings/{key} — настройка не найдена.

    Given: Настройка не существует
    When: GET /api/v1/settings/{key}
    Then: Возвращается ошибка 404
    """
    response = client.get("/api/v1/settings/nonexistent_key")

    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


def test_get_setting_value_typed(client: TestClient):
    """
    GET /api/v1/settings/{key}/value — типизированное значение.

    Given: Настройки разных типов существуют
    When: GET /api/v1/settings/{key}/value
    Then: Возвращается значение в правильном типе
    """
    # Создаем настройки разных типов
    settings = [
        {"key": "int_setting", "value": "42", "value_type": "int", "category": "operational"},
        {"key": "float_setting", "value": "3.14", "value_type": "float", "category": "operational"},
        {"key": "bool_setting", "value": "true", "value_type": "bool", "category": "operational"},
        {"key": "string_setting", "value": "hello", "value_type": "string", "category": "operational"}
    ]

    for setting in settings:
        client.post("/api/v1/settings", json=setting)

    # Проверяем типизированные значения
    # int
    response = client.get("/api/v1/settings/int_setting/value")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 42  # integer, не строка
    assert data["value_type"] == "int"

    # float
    response = client.get("/api/v1/settings/float_setting/value")
    data = response.json()
    assert data["value"] == 3.14  # float
    assert data["value_type"] == "float"

    # bool
    response = client.get("/api/v1/settings/bool_setting/value")
    data = response.json()
    assert data["value"] is True  # boolean
    assert data["value_type"] == "bool"

    # string
    response = client.get("/api/v1/settings/string_setting/value")
    data = response.json()
    assert data["value"] == "hello"  # строка
    assert data["value_type"] == "string"


def test_update_setting(client: TestClient):
    """
    PUT /api/v1/settings/{key} — обновление настройки.

    Given: Настройка существует
    When: PUT /api/v1/settings/{key}
    Then: Настройка обновляется
    """
    # Создаем настройку
    setting_data = {
        "key": "alert_threshold",
        "value": "1000",
        "value_type": "int",
        "category": "alerts"
    }
    client.post("/api/v1/settings", json=setting_data)

    # Обновляем значение
    update_data = {
        "value": "2000",
        "updated_by": "admin"
    }
    response = client.put("/api/v1/settings/alert_threshold", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "2000"
    assert data["updated_by"] == "admin"


def test_delete_setting(client: TestClient):
    """
    DELETE /api/v1/settings/{key} — удаление настройки.

    Given: Настройка существует
    When: DELETE /api/v1/settings/{key}
    Then: Настройка удаляется
    """
    # Создаем настройку
    setting_data = {
        "key": "temp_setting",
        "value": "temporary",
        "value_type": "string",
        "category": "operational"
    }
    client.post("/api/v1/settings", json=setting_data)

    # Удаляем настройку
    response = client.delete("/api/v1/settings/temp_setting")
    assert response.status_code == 204

    # Проверяем что удалилась
    response = client.get("/api/v1/settings/temp_setting")
    assert response.status_code == 404


def test_get_settings_by_category(client: TestClient):
    """
    GET /api/v1/settings/category/{category} — настройки по категории.

    Given: Настройки разных категорий существуют
    When: GET /api/v1/settings/category/{category}
    Then: Возвращаются только настройки этой категории
    """
    # Создаем настройки разных категорий
    settings = [
        {"key": "ai_model", "value": "gpt-4", "value_type": "string", "category": "ai"},
        {"key": "ai_temperature", "value": "0.7", "value_type": "float", "category": "ai"},
        {"key": "max_leads", "value": "100", "value_type": "int", "category": "operational"}
    ]

    for setting in settings:
        client.post("/api/v1/settings", json=setting)

    # Получаем настройки категории "ai"
    response = client.get("/api/v1/settings/category/ai")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # только 2 настройки категории "ai"

    keys = [setting["key"] for setting in data]
    assert "ai_model" in keys
    assert "ai_temperature" in keys
    assert "max_leads" not in keys


def test_bulk_update_settings(client: TestClient):
    """
    POST /api/v1/settings/bulk — массовое обновление настроек.

    Given: Массив настроек для создания/обновления
    When: POST /api/v1/settings/bulk
    Then: Все настройки создаются/обновляются
    """
    bulk_data = {
        "settings": [
            {"key": "bulk1", "value": "value1", "value_type": "string", "category": "ai"},
            {"key": "bulk2", "value": "42", "value_type": "int", "category": "ai"}
        ],
        "updated_by": "bulk_admin"
    }

    response = client.post("/api/v1/settings/bulk", json=bulk_data)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Проверяем что настройки созданы
    response1 = client.get("/api/v1/settings/bulk1")
    assert response1.status_code == 200
    assert response1.json()["updated_by"] == "bulk_admin"


def test_settings_validation_errors(client: TestClient):
    """
    Тестирование валидации настроек.

    Given: Некорректные данные настройки
    When: POST /api/v1/settings
    Then: Возвращается ошибка валидации
    """
    # Неверный тип значения
    invalid_settings = [
        {
            "key": "test",
            "value": "not_a_number",
            "value_type": "invalid_type",  # неверный тип
            "category": "ai"
        },
        {
            "key": "test2",
            "value": "value",
            "value_type": "string",
            "category": "invalid_category"  # неверная категория
        }
    ]

    for setting in invalid_settings:
        response = client.post("/api/v1/settings", json=setting)
        assert response.status_code == 422  # Validation error


def test_get_settings_with_filters(client: TestClient):
    """
    GET /api/v1/settings — фильтрация и поиск.

    Given: Настройки с разными категориями и ключами
    When: GET /api/v1/settings с параметрами фильтрации
    Then: Возвращаются отфильтрованные результаты
    """
    # Создаем тестовые настройки
    settings = [
        {"key": "openai_key", "value": "sk-123", "value_type": "string", "category": "ai", "description": "OpenAI API key"},
        {"key": "claude_key", "value": "sk-456", "value_type": "string", "category": "ai", "description": "Claude API key"},
        {"key": "max_budget", "value": "5000", "value_type": "int", "category": "financial", "description": "Maximum budget"}
    ]

    for setting in settings:
        client.post("/api/v1/settings", json=setting)

    # Фильтр по категории
    response = client.get("/api/v1/settings?category=ai")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2

    # Поиск по ключу
    response = client.get("/api/v1/settings?search=openai")
    data = response.json()
    assert data["total"] == 1
    assert data["settings"][0]["key"] == "openai_key"

    # Пагинация
    response = client.get("/api/v1/settings?page=1&page_size=2")
    data = response.json()
    assert len(data["settings"]) == 2
    assert data["page_size"] == 2
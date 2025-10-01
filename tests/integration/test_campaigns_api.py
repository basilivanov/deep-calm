"""
DeepCalm — Campaigns API Integration Tests

Тесты для CRUD операций campaigns API.
Следует TESTPLAN.md и DEEP-CALM-INFRASTRUCTURE.md
"""
import pytest
from fastapi.testclient import TestClient

from app.models.campaign import Campaign


def test_get_campaigns_empty(client: TestClient):
    """
    GET /api/v1/campaigns — пустой список.

    Given: БД пустая
    When: GET /api/v1/campaigns
    Then: Возвращается пустой список с total=0
    """
    response = client.get("/api/v1/campaigns")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


def test_create_campaign(client: TestClient):
    """
    POST /api/v1/campaigns — создание кампании.

    Given: Валидные данные кампании
    When: POST /api/v1/campaigns
    Then: Кампания создаётся со статусом 201
    """
    campaign_data = {
        "title": "Test Campaign",
        "sku": "RELAX-60",
        "budget_rub": 10000,
        "target_cac_rub": 500,
        "target_roas": 5.0,
        "channels": ["vk", "direct"]
    }

    response = client.post("/api/v1/campaigns", json=campaign_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Campaign"
    assert data["sku"] == "RELAX-60"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data


def test_create_campaign_invalid_channel(client: TestClient):
    """
    POST /api/v1/campaigns — невалидный канал.

    Given: Данные с неизвестным каналом
    When: POST /api/v1/campaigns
    Then: 422 Validation Error
    """
    campaign_data = {
        "title": "Test Campaign",
        "sku": "RELAX-60",
        "budget_rub": 10000,
        "channels": ["facebook"]  # невалидный канал
    }

    response = client.post("/api/v1/campaigns", json=campaign_data)

    assert response.status_code == 422
    assert "Недопустимые каналы" in response.text


def test_create_campaign_excluded_sku(client: TestClient):
    """
    POST /api/v1/campaigns — запрещённый SKU.

    Given: SKU из exclude_sku списка (TANTRA-120)
    When: POST /api/v1/campaigns
    Then: 422 Validation Error

    Согласно STANDARDS.yml: publishing.exclude_sku
    """
    campaign_data = {
        "title": "Test Campaign",
        "sku": "TANTRA-120",  # запрещён
        "budget_rub": 10000,
        "channels": ["vk"]
    }

    response = client.post("/api/v1/campaigns", json=campaign_data)

    assert response.status_code == 422
    assert "запрещён для публикации" in response.text


def test_get_campaign_by_id(client: TestClient, db_session):
    """
    GET /api/v1/campaigns/{id} — получение по ID.

    Given: Кампания существует в БД
    When: GET /api/v1/campaigns/{id}
    Then: Возвращается кампания
    """
    # Создаём кампанию напрямую в БД
    campaign = Campaign(
        title="Test Campaign",
        sku="RELAX-60",
        budget_rub=10000,
        channels=["vk"]
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    response = client.get(f"/api/v1/campaigns/{campaign.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(campaign.id)
    assert data["title"] == "Test Campaign"


def test_get_campaign_not_found(client: TestClient):
    """
    GET /api/v1/campaigns/{id} — несуществующий ID.

    Given: Кампании с таким ID нет
    When: GET /api/v1/campaigns/{id}
    Then: 404 Not Found
    """
    fake_id = "550e8400-e29b-41d4-a716-446655440000"
    response = client.get(f"/api/v1/campaigns/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_campaign(client: TestClient, db_session):
    """
    PATCH /api/v1/campaigns/{id} — обновление кампании.

    Given: Кампания существует
    When: PATCH /api/v1/campaigns/{id} с новыми данными
    Then: Кампания обновляется
    """
    # Создаём кампанию
    campaign = Campaign(
        title="Test Campaign",
        sku="RELAX-60",
        budget_rub=10000,
        channels=["vk"],
        status="draft"
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    # Обновляем
    update_data = {
        "status": "active",
        "budget_rub": 15000
    }

    response = client.patch(f"/api/v1/campaigns/{campaign.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["budget_rub"] == 15000
    assert data["title"] == "Test Campaign"  # не изменилось


def test_delete_campaign(client: TestClient, db_session):
    """
    DELETE /api/v1/campaigns/{id} — удаление кампании.

    Given: Кампания существует
    When: DELETE /api/v1/campaigns/{id}
    Then: 204 No Content, кампания удалена
    """
    # Создаём кампанию
    campaign = Campaign(
        title="Test Campaign",
        sku="RELAX-60",
        budget_rub=10000,
        channels=["vk"]
    )
    db_session.add(campaign)
    db_session.commit()
    campaign_id = campaign.id

    # Удаляем
    response = client.delete(f"/api/v1/campaigns/{campaign_id}")

    assert response.status_code == 204

    # Проверяем что удалена
    deleted = db_session.query(Campaign).filter(Campaign.id == campaign_id).first()
    assert deleted is None


def test_get_campaigns_pagination(client: TestClient, db_session):
    """
    GET /api/v1/campaigns — пагинация.

    Given: 5 кампаний в БД
    When: GET /api/v1/campaigns?page=1&page_size=2
    Then: Возвращается 2 элемента, total=5
    """
    # Создаём 5 кампаний
    for i in range(5):
        campaign = Campaign(
            title=f"Campaign {i+1}",
            sku="RELAX-60",
            budget_rub=10000,
            channels=["vk"]
        )
        db_session.add(campaign)
    db_session.commit()

    response = client.get("/api/v1/campaigns?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_get_campaigns_filter_by_status(client: TestClient, db_session):
    """
    GET /api/v1/campaigns?status=active — фильтр по статусу.

    Given: 3 кампании (2 active, 1 draft)
    When: GET /api/v1/campaigns?status=active
    Then: Возвращается 2 кампании
    """
    # Создаём кампании
    for status in ["active", "active", "draft"]:
        campaign = Campaign(
            title=f"Campaign {status}",
            sku="RELAX-60",
            budget_rub=10000,
            channels=["vk"],
            status=status
        )
        db_session.add(campaign)
    db_session.commit()

    response = client.get("/api/v1/campaigns?status=active")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["status"] == "active" for item in data["items"])

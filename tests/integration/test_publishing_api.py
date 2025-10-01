"""
Интеграционные тесты для Publishing API
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.creative import Creative


def test_publish_campaign_success(client: TestClient, db_session: Session):
    """Тест успешной публикации кампании"""
    # Создаем кампанию
    campaign = Campaign(
        title="Тестовая кампания для публикации",
        sku="RELAX-60",
        budget_rub=15000,
        target_cac_rub=800,
        target_roas=3.0,
        channels=["vk", "direct"],
        status="active",
        ab_test_enabled=True
    )
    db_session.add(campaign)
    db_session.flush()

    # Создаем одобренные креативы
    creative_a = Creative(
        campaign_id=campaign.id,
        variant="A",
        title="Релакс массаж — глубокое расслабление",
        body="60 минут блаженства. Забудьте о стрессе.",
        image_url="https://example.com/relax_a.jpg",
        cta="Записаться",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    creative_b = Creative(
        campaign_id=campaign.id,
        variant="B",
        title="Массаж для снятия напряжения",
        body="Профессиональный массаж 60 минут.",
        image_url="https://example.com/relax_b.jpg",
        cta="Узнать больше",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    db_session.add_all([creative_a, creative_b])
    db_session.commit()

    # Публикуем кампанию
    response = client.post(
        "/api/v1/publishing/publish",
        json={
            "campaign_id": str(campaign.id),
            "channels": ["vk", "direct"]
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["campaign_id"] == str(campaign.id)
    assert data["success_count"] == 4  # 2 креатива × 2 канала
    assert data["failed_count"] == 0
    assert len(data["placements"]) == 4

    # Проверяем структуру placements
    for placement in data["placements"]:
        assert "placement_id" in placement
        assert placement["channel"] in ["vk", "direct"]
        assert placement["creative_variant"] in ["A", "B"]
        assert placement["external_id"].startswith("vk_camp_") or placement["external_id"].startswith("direct_camp_")
        assert placement["status"] == "active"


def test_publish_campaign_without_channels(client: TestClient, db_session: Session):
    """Тест публикации кампании без указания каналов (использует channels из кампании)"""
    # Создаем кампанию
    campaign = Campaign(
        title="Кампания без каналов в запросе",
        sku="DEEP-90",
        budget_rub=25000,
        target_cac_rub=1000,
        target_roas=4.0,
        channels=["avito"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.flush()

    # Создаем одобренный креатив
    creative = Creative(
        campaign_id=campaign.id,
        variant="A",
        title="Глубокий массаж 90 минут",
        body="Проработка всех групп мышц.",
        image_url="https://example.com/deep.jpg",
        cta="Записаться",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    db_session.add(creative)
    db_session.commit()

    # Публикуем без указания channels
    response = client.post(
        "/api/v1/publishing/publish",
        json={
            "campaign_id": str(campaign.id)
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["success_count"] == 1  # 1 креатив × 1 канал (avito)
    assert data["placements"][0]["channel"] == "avito"
    assert data["placements"][0]["external_id"].startswith("avito_ad_")


def test_publish_campaign_not_found(client: TestClient):
    """Тест публикации несуществующей кампании"""
    response = client.post(
        "/api/v1/publishing/publish",
        json={
            "campaign_id": "00000000-0000-0000-0000-000000000000",
            "channels": ["vk"]
        }
    )

    assert response.status_code == 400
    assert "не найдена" in response.json()["detail"]


def test_publish_campaign_no_approved_creatives(client: TestClient, db_session: Session):
    """Тест публикации кампании без одобренных креативов"""
    campaign = Campaign(
        title="Кампания без креативов",
        sku="RELAX-60",
        budget_rub=10000,
        target_cac_rub=800,
        target_roas=3.0,
        channels=["vk"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.flush()

    # Создаем креатив на модерации
    creative = Creative(
        campaign_id=campaign.id,
        variant="A",
        title="Креатив на модерации",
        body="Тест",
        image_url="https://example.com/test.jpg",
        cta="Тест",
        generated_by="mock_llm",
        moderation_status="pending"
    )
    db_session.add(creative)
    db_session.commit()

    response = client.post(
        "/api/v1/publishing/publish",
        json={
            "campaign_id": str(campaign.id),
            "channels": ["vk"]
        }
    )

    assert response.status_code == 400
    assert "Нет одобренных креативов" in response.json()["detail"]


def test_get_publishing_status_success(client: TestClient, db_session: Session):
    """Тест получения статуса публикации кампании"""
    # Создаем кампанию
    campaign = Campaign(
        title="Кампания для проверки статуса",
        sku="RELAX-60",
        budget_rub=15000,
        target_cac_rub=800,
        target_roas=3.0,
        channels=["vk"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.flush()

    # Создаем одобренный креатив
    creative = Creative(
        campaign_id=campaign.id,
        variant="A",
        title="Тестовый креатив",
        body="Описание",
        image_url="https://example.com/test.jpg",
        cta="Записаться",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    db_session.add(creative)
    db_session.commit()

    # Публикуем
    publish_response = client.post(
        "/api/v1/publishing/publish",
        json={
            "campaign_id": str(campaign.id),
            "channels": ["vk"]
        }
    )
    assert publish_response.status_code == 201

    # Получаем статус
    response = client.get(f"/api/v1/publishing/status/{campaign.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["campaign_id"] == str(campaign.id)
    assert data["campaign_title"] == "Кампания для проверки статуса"
    assert data["total_placements"] == 1
    assert data["active_placements"] == 1
    assert data["paused_placements"] == 0
    assert data["failed_placements"] == 0
    assert len(data["placements"]) == 1


def test_get_publishing_status_not_found(client: TestClient):
    """Тест получения статуса несуществующей кампании"""
    response = client.get("/api/v1/publishing/status/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


def test_pause_campaign_success(client: TestClient, db_session: Session):
    """Тест приостановки кампании"""
    # Создаем кампанию
    campaign = Campaign(
        title="Кампания для приостановки",
        sku="DEEP-90",
        budget_rub=20000,
        target_cac_rub=1000,
        target_roas=3.5,
        channels=["vk", "direct"],
        status="active",
        ab_test_enabled=True
    )
    db_session.add(campaign)
    db_session.flush()

    # Создаем одобренные креативы
    creative_a = Creative(
        campaign_id=campaign.id,
        variant="A",
        title="Креатив A",
        body="Описание A",
        image_url="https://example.com/a.jpg",
        cta="Записаться",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    creative_b = Creative(
        campaign_id=campaign.id,
        variant="B",
        title="Креатив B",
        body="Описание B",
        image_url="https://example.com/b.jpg",
        cta="Узнать больше",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    db_session.add_all([creative_a, creative_b])
    db_session.commit()

    # Публикуем
    publish_response = client.post(
        "/api/v1/publishing/publish",
        json={
            "campaign_id": str(campaign.id),
            "channels": ["vk", "direct"]
        }
    )
    assert publish_response.status_code == 201

    # Приостанавливаем
    response = client.post(f"/api/v1/publishing/pause/{campaign.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["campaign_id"] == str(campaign.id)
    assert data["paused_count"] == 4  # 2 креатива × 2 канала
    assert data["failed_count"] == 0
    assert "Приостановлено: 4" in data["message"]

    # Проверяем статус после приостановки
    status_response = client.get(f"/api/v1/publishing/status/{campaign.id}")
    status_data = status_response.json()

    assert status_data["active_placements"] == 0
    assert status_data["paused_placements"] == 4


def test_pause_campaign_not_found(client: TestClient):
    """Тест приостановки несуществующей кампании"""
    response = client.post("/api/v1/publishing/pause/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


def test_pause_campaign_no_active_placements(client: TestClient, db_session: Session):
    """Тест приостановки кампании без активных размещений"""
    campaign = Campaign(
        title="Кампания без размещений",
        sku="RELAX-60",
        budget_rub=10000,
        target_cac_rub=800,
        target_roas=3.0,
        channels=["vk"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.commit()

    # Приостанавливаем кампанию без размещений
    response = client.post(f"/api/v1/publishing/pause/{campaign.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["paused_count"] == 0
    assert data["failed_count"] == 0

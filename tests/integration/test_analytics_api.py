"""
Интеграционные тесты для Analytics API
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.conversion import Conversion
from app.models.creative import Creative
from app.models.lead import Lead
from app.models.placement import Placement


def test_get_campaign_analytics_success(client: TestClient, db_session: Session):
    """Тест получения аналитики по кампании"""
    # Создаем кампанию
    campaign = Campaign(
        title="Тестовая кампания для аналитики",
        sku="RELAX-60",
        budget_rub=20000,
        target_cac_rub=800,
        target_roas=4.0,
        channels=["vk", "direct"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.flush()

    # Создаем креатив
    creative = Creative(
        campaign_id=campaign.id,
        variant="A",
        title="Релакс массаж",
        body="Описание",
        image_url="https://example.com/test.jpg",
        cta="Записаться",
        generated_by="mock_llm",
        moderation_status="approved"
    )
    db_session.add(creative)
    db_session.flush()

    # Создаем placements
    placement_vk = Placement(
        campaign_id=campaign.id,
        creative_id=creative.id,
        channel_code="vk",
        external_campaign_id="vk_123",
        status="active",
        published_at=datetime.now(timezone.utc)
    )
    placement_direct = Placement(
        campaign_id=campaign.id,
        creative_id=creative.id,
        channel_code="direct",
        external_campaign_id="direct_456",
        status="active",
        published_at=datetime.now(timezone.utc)
    )
    db_session.add_all([placement_vk, placement_direct])

    # Создаем лиды
    lead1 = Lead(
        phone="+79991234567",
        utm_source="vk_ads",
        utm_medium="cpc",
        utm_campaign=campaign.title
    )
    db_session.add(lead1)
    db_session.flush()

    # Создаем конверсию
    conversion1 = Conversion(
        campaign_id=campaign.id,
        lead_id=lead1.id,
        booking_id=12345,
        revenue_rub=3500.0,
        converted_at=datetime.now(timezone.utc)
    )
    db_session.add(conversion1)
    db_session.commit()

    # Получаем аналитику
    response = client.get(f"/api/v1/analytics/campaigns/{campaign.id}")

    assert response.status_code == 200
    data = response.json()

    # Проверяем метрики
    metrics = data["metrics"]
    assert metrics["campaign_id"] == str(campaign.id)
    assert metrics["campaign_title"] == "Тестовая кампания для аналитики"
    assert metrics["sku"] == "RELAX-60"
    assert metrics["budget_rub"] == 20000
    assert metrics["target_cac_rub"] == 800
    assert metrics["target_roas"] == 4.0

    assert metrics["leads_count"] == 1
    assert metrics["conversions_count"] == 1
    assert metrics["conversion_rate"] == 100.0
    assert metrics["revenue_rub"] == 3500.0

    # Проверяем что есть calculated метрики
    assert metrics["spent_rub"] > 0
    assert metrics["actual_cac_rub"] is not None
    assert metrics["actual_roas"] is not None

    # Проверяем разбивку по каналам
    channels = data["channels"]
    assert len(channels) == 2

    channel_codes = [c["channel_code"] for c in channels]
    assert "vk" in channel_codes
    assert "direct" in channel_codes


def test_get_campaign_analytics_not_found(client: TestClient):
    """Тест получения аналитики несуществующей кампании"""
    response = client.get("/api/v1/analytics/campaigns/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


def test_get_campaign_analytics_with_date_filter(client: TestClient, db_session: Session):
    """Тест получения аналитики с фильтрацией по датам"""
    # Создаем кампанию
    campaign = Campaign(
        title="Кампания с датами",
        sku="DEEP-90",
        budget_rub=30000,
        target_cac_rub=1000,
        target_roas=3.5,
        channels=["vk"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.commit()

    # Получаем аналитику с датами
    response = client.get(
        f"/api/v1/analytics/campaigns/{campaign.id}",
        params={
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["campaign_id"] == str(campaign.id)


def test_get_dashboard_summary_empty(client: TestClient, db_session: Session):
    """Тест получения сводки дашборда без кампаний"""
    # Удаляем все кампании (если есть)
    db_session.query(Campaign).delete()
    db_session.commit()

    response = client.get("/api/v1/analytics/dashboard")

    assert response.status_code == 200
    data = response.json()

    assert data["total_campaigns"] == 0
    assert data["active_campaigns"] == 0
    assert data["paused_campaigns"] == 0
    assert data["total_budget_rub"] == 0
    assert data["total_spent_rub"] == 0
    assert data["total_leads"] == 0
    assert data["total_conversions"] == 0
    assert data["total_revenue_rub"] == 0


def test_get_dashboard_summary_with_campaigns(client: TestClient, db_session: Session):
    """Тест получения сводки дашборда с кампаниями"""
    # Создаем несколько кампаний
    campaign1 = Campaign(
        title="Кампания 1",
        sku="RELAX-60",
        budget_rub=15000,
        target_cac_rub=800,
        target_roas=3.0,
        channels=["vk"],
        status="active",
        ab_test_enabled=False
    )
    campaign2 = Campaign(
        title="Кампания 2",
        sku="DEEP-90",
        budget_rub=25000,
        target_cac_rub=1000,
        target_roas=4.0,
        channels=["direct"],
        status="paused",
        ab_test_enabled=False
    )
    db_session.add_all([campaign1, campaign2])
    db_session.flush()

    # Добавляем лиды к первой кампании
    lead1 = Lead(
        phone="+79991111111",
        utm_source="vk_ads",
        utm_medium="cpc",
        utm_campaign=campaign1.title
    )
    lead2 = Lead(
        phone="+79992222222",
        utm_source="vk_ads",
        utm_medium="cpc",
        utm_campaign=campaign1.title
    )
    db_session.add_all([lead1, lead2])
    db_session.flush()

    # Добавляем конверсии
    conversion1 = Conversion(
        campaign_id=campaign1.id,
        lead_id=lead1.id,
        booking_id=99999,
        revenue_rub=3500.0,
        converted_at=datetime.now(timezone.utc)
    )
    conversion2 = Conversion(
        campaign_id=campaign1.id,
        lead_id=lead2.id,
        booking_id=99998,
        revenue_rub=3500.0,
        converted_at=datetime.now(timezone.utc)
    )
    db_session.add_all([conversion1, conversion2])
    db_session.commit()

    # Получаем сводку
    response = client.get("/api/v1/analytics/dashboard")

    assert response.status_code == 200
    data = response.json()

    assert data["total_campaigns"] == 2
    assert data["active_campaigns"] == 1
    assert data["paused_campaigns"] == 1
    assert data["total_budget_rub"] == 40000  # 15000 + 25000
    assert data["total_leads"] >= 2
    assert data["total_conversions"] >= 2
    assert data["total_revenue_rub"] >= 7000.0  # 3500 * 2


def test_get_dashboard_summary_with_date_filter(client: TestClient, db_session: Session):
    """Тест получения сводки дашборда с фильтрацией по датам"""
    # Создаем кампанию
    campaign = Campaign(
        title="Кампания для сводки",
        sku="RELAX-60",
        budget_rub=10000,
        target_cac_rub=700,
        target_roas=3.0,
        channels=["avito"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.commit()

    # Получаем сводку с датами
    response = client.get(
        "/api/v1/analytics/dashboard",
        params={
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_campaigns"] >= 1


def test_campaign_metrics_cac_status(client: TestClient, db_session: Session):
    """Тест расчета статуса CAC"""
    campaign = Campaign(
        title="Кампания для CAC теста",
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

    # Добавляем лид и конверсию для расчета CAC
    lead = Lead(
        phone="+79993333333",
        utm_source="vk_ads",
        utm_medium="cpc",
        utm_campaign=campaign.title
    )
    db_session.add(lead)
    db_session.flush()

    conversion = Conversion(
        campaign_id=campaign.id,
        lead_id=lead.id,
        booking_id=88888,
        revenue_rub=3000.0,
        converted_at=datetime.now(timezone.utc)
    )
    db_session.add(conversion)
    db_session.commit()

    response = client.get(f"/api/v1/analytics/campaigns/{campaign.id}")

    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    # CAC должен быть рассчитан
    assert metrics["actual_cac_rub"] is not None
    # Статус должен быть определен
    assert metrics["cac_status"] in ["on_track", "over_target", "under_target", "unknown"]


def test_campaign_metrics_roas_status(client: TestClient, db_session: Session):
    """Тест расчета статуса ROAS"""
    campaign = Campaign(
        title="Кампания для ROAS теста",
        sku="DEEP-90",
        budget_rub=20000,
        target_cac_rub=1000,
        target_roas=4.0,
        channels=["direct"],
        status="active",
        ab_test_enabled=False
    )
    db_session.add(campaign)
    db_session.flush()

    # Добавляем лид и конверсию для расчета ROAS
    lead = Lead(
        phone="+79994444444",
        utm_source="yandex_direct",
        utm_medium="cpc",
        utm_campaign=campaign.title
    )
    db_session.add(lead)
    db_session.flush()

    conversion = Conversion(
        campaign_id=campaign.id,
        lead_id=lead.id,
        booking_id=77777,
        revenue_rub=5000.0,
        converted_at=datetime.now(timezone.utc)
    )
    db_session.add(conversion)
    db_session.commit()

    response = client.get(f"/api/v1/analytics/campaigns/{campaign.id}")

    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    # ROAS должен быть рассчитан
    assert metrics["actual_roas"] is not None
    # Статус должен быть определен
    assert metrics["roas_status"] in ["on_track", "over_target", "under_target", "unknown"]


def test_get_dashboard_daily_metrics(client: TestClient, db_session: Session):
    """Проверяем, что endpoint ежедневных метрик возвращает данные."""

    campaign = Campaign(
        title="Daily Stats",
        sku="RELAX-30",
        budget_rub=10000,
        target_cac_rub=600,
        target_roas=3.0,
        channels=["direct"],
        status="active",
        ab_test_enabled=False,
    )
    db_session.add(campaign)
    db_session.flush()

    lead = Lead(
        phone="+79995555555",
        utm_source="yandex_direct",
        utm_medium="cpc",
        utm_campaign=campaign.title,
    )
    db_session.add(lead)
    db_session.flush()

    conversion = Conversion(
        campaign_id=campaign.id,
        lead_id=lead.id,
        booking_id=555,
        revenue_rub=4000.0,
        converted_at=datetime.now(timezone.utc),
    )
    db_session.add(conversion)
    db_session.commit()

    response = client.get("/api/v1/analytics/dashboard/daily")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert data, "Ожидаем хотя бы одну точку в ежедневных метриках"

    sample = data[-1]
    assert "date" in sample
    assert "conversions" in sample
    assert "revenue" in sample
    assert "spend" in sample


def test_get_dashboard_channel_performance(client: TestClient, db_session: Session):
    """Проверяем, что endpoint метрик каналов возвращает агрегацию."""

    campaign = Campaign(
        title="Channel Stats",
        sku="DEEP-60",
        budget_rub=12000,
        target_cac_rub=700,
        target_roas=3.5,
        channels=["vk", "direct"],
        status="active",
        ab_test_enabled=False,
    )
    db_session.add(campaign)
    db_session.flush()

    lead_vk = Lead(
        phone="+79997777777",
        utm_source="vk_ads",
        utm_medium="cpc",
        utm_campaign=campaign.title,
    )
    lead_direct = Lead(
        phone="+79998888888",
        utm_source="yandex_direct",
        utm_medium="cpc",
        utm_campaign=campaign.title,
    )
    db_session.add_all([lead_vk, lead_direct])
    db_session.flush()

    conversion_vk = Conversion(
        campaign_id=campaign.id,
        lead_id=lead_vk.id,
        booking_id=444,
        revenue_rub=3500.0,
        channel_code="vk",
        converted_at=datetime.now(timezone.utc),
    )
    conversion_direct = Conversion(
        campaign_id=campaign.id,
        lead_id=lead_direct.id,
        booking_id=333,
        revenue_rub=3600.0,
        channel_code="direct",
        converted_at=datetime.now(timezone.utc),
    )
    db_session.add_all([conversion_vk, conversion_direct])
    db_session.commit()

    response = client.get("/api/v1/analytics/dashboard/channels")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    channel_codes = {item["channel"] for item in data}
    assert "vk" in channel_codes
    assert "direct" in channel_codes

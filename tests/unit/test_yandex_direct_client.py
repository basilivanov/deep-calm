import json
from datetime import date
from typing import Any, Dict

import httpx
import pytest

from app.integrations.yandex_direct import YandexDirectClient, YandexDirectError


class _FakeResponse(httpx.Response):
    def __init__(self, status_code: int, payload: Dict[str, Any], url: str) -> None:
        request = httpx.Request("POST", url)
        super().__init__(status_code, json=payload, request=request)


def test_create_campaign_mock_mode(monkeypatch):
    client = YandexDirectClient(token=None, login=None)
    result = client.create_campaign(title="Test", body="", image_url="", budget_rub=100)
    assert result.startswith("direct_camp_")


def test_create_campaign_real(monkeypatch):
    captured = {}

    def fake_post(url: str, headers: Dict[str, Any], json: Dict[str, Any], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse(200, {"result": {"AddResults": [{"Id": 987654321}]}} , url)

    monkeypatch.setattr("app.integrations.yandex_direct.httpx.post", fake_post)

    client = YandexDirectClient(token="token", login="client", sandbox=True)
    campaign_id = client.create_campaign(title="Demo", body="", image_url="", budget_rub=50)

    assert campaign_id == "987654321"
    assert captured["url"] == "https://api-sandbox.direct.yandex.com/json/v5/campaigns"
    assert captured["json"]["method"] == "add"
    assert "Campaigns" in captured["json"]["params"]
    assert captured["headers"]["Authorization"] == "Bearer token"
    assert captured["headers"]["Client-Login"] == "client"

    # Проверяем исправления: корректный расчет бюджета и StartDate
    campaign = captured["json"]["params"]["Campaigns"][0]
    assert campaign["StartDate"] == date.today().strftime("%Y-%m-%d")
    assert campaign["DailyBudget"]["Amount"] == 300000000  # min(max(50/30, 300), 10000) * 1000000 = 300 * 1000000


def test_create_campaign_error(monkeypatch):
    def fake_post(url: str, headers: Dict[str, Any], json: Dict[str, Any], timeout: float):
        return _FakeResponse(400, {"error": {"error_code": 91, "error_detail": "Bad Request"}}, url)

    monkeypatch.setattr("app.integrations.yandex_direct.httpx.post", fake_post)

    client = YandexDirectClient(token="token", login="client")

    with pytest.raises(YandexDirectError) as exc:
        client.create_campaign(title="Demo", body="", image_url="", budget_rub=50)

    assert "Ошибка HTTP" in str(exc.value)


def test_pause_resume_mock():
    client = YandexDirectClient(token=None, login=None)
    assert client.pause_campaign("123") == {"status": "paused"}
    assert client.resume_campaign("123") == {"status": "active"}


def test_budget_calculation_limits(monkeypatch):
    """Тест проверяет правильность расчета бюджета с лимитами"""
    captured = {}

    def fake_post(url: str, headers: Dict[str, Any], json: Dict[str, Any], timeout: float):
        captured["json"] = json
        return _FakeResponse(200, {"result": {"AddResults": [{"Id": 123}]}}, url)

    monkeypatch.setattr("app.integrations.yandex_direct.httpx.post", fake_post)
    client = YandexDirectClient(token="token", sandbox=True)

    # Маленький бюджет: 50 руб -> daily = max(50/30, 300) = 300
    client.create_campaign(title="Small", body="", image_url="", budget_rub=50)
    campaign = captured["json"]["params"]["Campaigns"][0]
    assert campaign["DailyBudget"]["Amount"] == 300000000  # 300 * 1000000

    # Большой бюджет: 500000 руб -> daily = min(max(500000/30, 300), 10000) = 10000
    client.create_campaign(title="Large", body="", image_url="", budget_rub=500000)
    campaign = captured["json"]["params"]["Campaigns"][0]
    assert campaign["DailyBudget"]["Amount"] == 10000000000  # 10000 * 1000000

    # Средний бюджет: 15000 руб -> daily = min(max(15000/30, 300), 10000) = 500
    client.create_campaign(title="Medium", body="", image_url="", budget_rub=15000)
    campaign = captured["json"]["params"]["Campaigns"][0]
    assert campaign["DailyBudget"]["Amount"] == 500000000  # 500 * 1000000

import json
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

"""DeepCalm — интеграция с Яндекс.Директ API v5."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict

import httpx
import structlog

logger = structlog.get_logger(__name__)


YANDEX_API_URL = "https://api.direct.yandex.com/json/v5/"
YANDEX_SANDBOX_URL = "https://api-sandbox.direct.yandex.com/json/v5/"


class YandexDirectError(RuntimeError):
    """Исключение для ошибок Яндекс.Директа."""

    def __init__(self, message: str, *, payload: Dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {}


@dataclass
class YandexDirectClient:
    """Клиент для работы с JSON API Яндекс.Директа.

    Если токен или логин не переданы, клиент работает в mock-режиме
    (используется в dev/test окружениях без реальных ключей).
    """

    token: str | None = None
    login: str | None = None
    sandbox: bool = True
    language: str = "ru"
    timeout: float = 15.0

    def __post_init__(self) -> None:
        self._enabled = bool(self.token and self.login)
        self._base_url = YANDEX_SANDBOX_URL if self.sandbox else YANDEX_API_URL

        mode = "real" if self._enabled else "mock"
        logger.info(
            "yandex_direct_client_initialized",
            mode=mode,
            sandbox=self.sandbox,
        )

    # ------------------------------------------------------------------
    # Основные операции
    # ------------------------------------------------------------------
    def create_campaign(self, *, title: str, body: str, image_url: str, budget_rub: float) -> str:
        """Создаёт текстовую кампанию в Яндекс.Директ.

        В реальном режиме отправляет запрос `campaigns/add` и возвращает ID кампании.
        В mock-режиме создаёт псевдо-ID (для локальной разработки).
        """

        if not self._enabled:
            campaign_id = f"direct_camp_{uuid.uuid4().hex[:8]}"
            logger.info("yandex_direct_mock_create", campaign_id=campaign_id)
            return campaign_id

        params = self._build_text_campaign_payload(title=title, budget_rub=budget_rub)
        result = self._request("campaigns", "add", params)

        add_results = result.get("AddResults", [])
        if not add_results:
            raise YandexDirectError("Пустой ответ при создании кампании", payload=result)

        campaign_id = add_results[0].get("Id")
        if campaign_id is None:
            raise YandexDirectError("Не удалось получить Id кампании", payload=add_results[0])

        logger.info("yandex_direct_campaign_created", campaign_id=campaign_id)
        return str(campaign_id)

    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        if not self._enabled:
            logger.info("yandex_direct_mock_pause", campaign_id=campaign_id)
            return {"status": "paused"}

        self._request("campaigns", "suspend", {"CampaignIds": [int(campaign_id)]})
        logger.info("yandex_direct_campaign_paused", campaign_id=campaign_id)
        return {"status": "paused"}

    def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        if not self._enabled:
            logger.info("yandex_direct_mock_resume", campaign_id=campaign_id)
            return {"status": "active"}

        self._request("campaigns", "resume", {"CampaignIds": [int(campaign_id)]})
        logger.info("yandex_direct_campaign_resumed", campaign_id=campaign_id)
        return {"status": "active"}

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    def _request(self, service: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}{service}"
        payload = {"method": method, "params": params}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Client-Login": self.login or "",
            "Accept-Language": self.language,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "DeepCalm/1.0",
        }

        logger.debug(
            "yandex_direct_request",
            url=url,
            method=method,
            payload=payload,
        )

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise YandexDirectError(f"Ошибка HTTP при обращении к {service}/{method}: {exc}") from exc

        data = response.json()

        if "error" in data:
            raise YandexDirectError(
                "Ошибка Яндекс.Директ",
                payload=data["error"],
            )

        result = data.get("result")
        if result is None:
            raise YandexDirectError("Ответ не содержит result", payload=data)

        return result

    @staticmethod
    def _build_text_campaign_payload(*, title: str, budget_rub: float) -> Dict[str, Any]:
        normalized_title = title[:255] if title else "DeepCalm campaign"
        amount_micros = str(max(int(budget_rub * 1_000_000), 1_000_000))

        return {
            "Campaigns": [
                {
                    "Name": normalized_title,
                    "DailyBudget": {"Amount": amount_micros, "Mode": "STANDARD"},
                    "TextCampaign": {
                        "BiddingStrategy": {
                            "Search": {"BiddingStrategyType": "SERVING_OFF"},
                            "Network": {"BiddingStrategyType": "MAXIMUM_COVERAGE"},
                        },
                        "Settings": [
                            {"Option": "ADD_TO_FAVORITES", "Value": "YES"},
                            {"Option": "ENABLE_AREA_OF_INTEREST_TARGETING", "Value": "NO"},
                        ],
                    },
                }
            ]
        }

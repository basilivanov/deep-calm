"""DeepCalm — интеграция с Яндекс.Директ API v5."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List

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
        self._enabled = bool(self.token)
        self._base_url = YANDEX_SANDBOX_URL if self.sandbox else YANDEX_API_URL

        # Убираем login если пустой (роль "Клиент")
        if self.login and not self.login.strip():
            self.login = None

        mode = "real" if self._enabled else "mock"
        role = "agency" if self.login else "client"
        logger.info(
            "yandex_direct_client_initialized",
            mode=mode,
            sandbox=self.sandbox,
            role=role,
            has_login=bool(self.login),
        )

    # ------------------------------------------------------------------
    # Основные операции
    # ------------------------------------------------------------------
    def create_campaign(
        self, *, title: str, body: str, image_url: str, budget_rub: float
    ) -> str:
        """Создаёт текстовую кампанию в Яндекс.Директ.

        В реальном режиме отправляет запрос `campaigns/add` и возвращает ID кампании.
        В mock-режиме создаёт псевдо-ID (для локальной разработки).
        """
        logger.info(
            "yandex_direct_create_campaign_started",
            title=title,
            budget_rub=budget_rub,
            enabled=self._enabled,
            sandbox=self.sandbox,
        )

        if not self._enabled:
            campaign_id = f"direct_camp_{uuid.uuid4().hex[:8]}"
            logger.info("yandex_direct_mock_create", campaign_id=campaign_id)
            return campaign_id

        params = self._build_text_campaign_payload(title=title, budget_rub=budget_rub)
        logger.info("yandex_direct_payload_built", params=params)

        result = self._request("campaigns", "add", params)

        add_results = result.get("AddResults", [])
        if not add_results:
            raise YandexDirectError(
                "Пустой ответ при создании кампании", payload=result
            )

        campaign_id = add_results[0].get("Id")
        if campaign_id is None:
            raise YandexDirectError(
                "Не удалось получить Id кампании", payload=add_results[0]
            )

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

    def get_campaigns(self) -> List[Dict[str, Any]]:
        """Получает список кампаний из Яндекс.Директ.

        Returns:
            Список кампаний с полями Id, Name, Status, State
        """
        if not self._enabled:
            # Mock данные для разработки
            mock_campaigns = [
                {
                    "Id": 700005747,
                    "Name": "Test API Sandbox campaign 1",
                    "Status": "ACCEPTED",
                    "State": "ON",
                    "Type": "TEXT_CAMPAIGN",
                }
            ]
            logger.info("yandex_direct_mock_get_campaigns", count=len(mock_campaigns))
            return mock_campaigns

        params = {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State", "Type"],
        }

        result = self._request("campaigns", "get", params)
        campaigns = result.get("Campaigns", [])

        logger.info("yandex_direct_campaigns_retrieved", count=len(campaigns))
        return campaigns

    def health_check(self) -> Dict[str, Any]:
        """Проверяет подключение к API Яндекс.Директ.

        Returns:
            Статус подключения и информация о аккаунте
        """
        if not self._enabled:
            return {
                "status": "mock_mode",
                "message": "Работает в режиме mock (токен не настроен)",
                "role": "mock",
            }

        try:
            campaigns = self.get_campaigns()
            return {
                "status": "ok",
                "message": f"Подключение работает. Найдено кампаний: {len(campaigns)}",
                "role": "agency" if self.login else "client",
                "campaigns_count": len(campaigns),
                "sandbox": self.sandbox,
            }
        except Exception as e:
            logger.error("yandex_direct_health_check_failed", error=str(e))
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}",
                "role": "agency" if self.login else "client",
            }

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    def _request(
        self, service: str, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = f"{self._base_url}{service}"
        payload = {"method": method, "params": params}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept-Language": self.language,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "DeepCalm/1.0",
        }
        if self.login:
            headers["Client-Login"] = self.login

        logger.debug(
            "yandex_direct_request",
            url=url,
            method=method,
            payload=payload,
        )

        try:
            response = httpx.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise YandexDirectError(
                f"Ошибка HTTP при обращении к {service}/{method}: {exc}"
            ) from exc

        data = response.json()

        logger.info(
            "yandex_direct_response",
            url=url,
            method=method,
            status_code=response.status_code,
            response_data=data,
        )

        if "error" in data:
            error_details = data["error"]
            logger.error(
                "yandex_direct_api_error",
                service=service,
                method=method,
                error_code=error_details.get("error_code"),
                error_string=error_details.get("error_string"),
                error_detail=error_details.get("error_detail"),
                request_id=error_details.get("request_id"),
            )
            raise YandexDirectError(
                f"Яндекс.Директ API ошибка: {error_details.get('error_string', 'Unknown')}",
                payload=error_details,
            )

        result = data.get("result")
        if result is None:
            raise YandexDirectError("Ответ не содержит result", payload=data)

        return result

    @staticmethod
    def _build_text_campaign_payload(
        *, title: str, budget_rub: float
    ) -> Dict[str, Any]:
        """Создает payload для создания текстовой кампании в API v5.

        Структура соответствует документации:
        https://yandex.ru/dev/direct/doc/ref-v5/campaigns/add.html
        """
        normalized_title = title[:255] if title else "DeepCalm campaign"
        # Дневной бюджет в валюте * 1_000_000, но ограничиваем разумными пределами для sandbox
        # Используем минимум 300 руб/день, максимум 10000 руб/день
        daily_budget_rub = min(
            max(budget_rub / 30, 300), 10000
        )  # предполагаем что budget_rub - месячный
        amount_micros = int(daily_budget_rub * 1_000_000)

        logger.info(
            "yandex_direct_budget_calculation",
            original_budget_rub=budget_rub,
            daily_budget_rub=daily_budget_rub,
            amount_micros=amount_micros,
        )
        # Updated budget calculation logic - fixed 5 billion issue

        return {
            "Campaigns": [
                {
                    "Name": normalized_title,
                    "StartDate": date.today().strftime("%Y-%m-%d"),  # Начинаем сегодня
                    "DailyBudget": {"Amount": amount_micros, "Mode": "STANDARD"},
                    "TextCampaign": {
                        "BiddingStrategy": {
                            "Search": {"BiddingStrategyType": "HIGHEST_POSITION"},
                            "Network": {"BiddingStrategyType": "SERVING_OFF"},
                        },
                        "Settings": [
                            {"Option": "ADD_TO_FAVORITES", "Value": "YES"},
                            {"Option": "ENABLE_COMPANY_INFO", "Value": "YES"},
                            {"Option": "ENABLE_SITE_MONITORING", "Value": "YES"},
                        ],
                    },
                }
            ]
        }

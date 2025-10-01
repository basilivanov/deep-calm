# DeepCalm — Logging Standards

## Общие правила

### Формат: JSON (structlog)
```python
import structlog

logger = structlog.get_logger()
logger.info("campaign_created", campaign_id=campaign.id, channels=campaign.channels, sku=campaign.sku)
```

### Обязательные поля в каждом логе:
- `ts` — ISO8601 timestamp
- `level` — INFO/WARNING/ERROR/CRITICAL
- `app` — "deep-calm"
- `svc` — "dc-api" / "dc-jobs"
- `env` — "dev" / "test" / "prod"
- `req_id` — request ID (для трассировки)

### PII Masking (обязательно!)
```python
import re

def mask_pii(_, __, event_dict):
    """Маскируем телефоны и email в логах"""
    for key, value in event_dict.items():
        if isinstance(value, str):
            # Телефоны: +79991234567 → +7999***4567
            value = re.sub(r'(\+7\d{3})\d{3}(\d{4})', r'\1***\2', value)
            # Email: vasya@example.com → v***a@example.com
            value = re.sub(r'(\w)\w+(\w)@', r'\1***\2@', value)
            event_dict[key] = value
    return event_dict

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        mask_pii,  # ← Обязательно!
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)
```

## Уровни логирования

### INFO
- Основные бизнес-события:
  - `campaign_created`, `campaign_published`, `campaign_paused`
  - `creative_generated`, `lead_created`, `conversion_tracked`
  - `analyst_report_generated`

### WARNING
- Ожидаемые проблемы:
  - `api_rate_limit_hit` (внешний API ограничил запросы)
  - `creative_moderation_rejected` (площадка отклонила креатив)
  - `cac_threshold_exceeded` (CAC выше целевого)

### ERROR
- Ошибки требующие внимания:
  - `integration_api_failed` (не удалось вызвать внешний API)
  - `database_query_failed`
  - `migration_failed`

### CRITICAL
- Критичные сбои:
  - `database_connection_lost`
  - `redis_unavailable`
  - `all_integrations_down`

## Контексты (contextvars)

Используй `contextvars` для автоматического добавления контекста:

```python
import contextvars
from uuid import uuid4

request_id_var = contextvars.ContextVar("request_id", default=None)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request_id_var.set(request_id)
    structlog.contextvars.bind_contextvars(req_id=request_id)
    response = await call_next(request)
    return response
```

Теперь все логи внутри запроса автоматически будут иметь `req_id`.

## Интеграции (внешние API)

Логируй ВСЕ вызовы внешних API:

```python
async def call_yandex_direct_api(method: str, params: dict):
    logger.info("direct_api_call_start", method=method)

    try:
        response = await httpx_client.post(
            "https://api.direct.yandex.com/json/v5/campaigns",
            json={"method": method, "params": params}
        )

        logger.info(
            "direct_api_call_success",
            method=method,
            status_code=response.status_code,
            response_time_ms=response.elapsed.total_seconds() * 1000
        )

        return response.json()

    except httpx.HTTPError as e:
        logger.error(
            "direct_api_call_failed",
            method=method,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

## Что НЕ логировать

❌ **Никогда не логируй:**
- Пароли
- API токены (даже частично)
- Полные номера телефонов (только маскированные)
- Email (только маскированные)
- Платёжные данные

❌ **Не логируй в DEBUG на production:**
- SQL-запросы с параметрами (там может быть PII)
- Полные тела HTTP-ответов

✅ **DEBUG только на dev:**
```python
if settings.APP_ENV == "dev":
    logger.debug("sql_query", query=query, params=params)
```

## Примеры правильных логов

### Campaign создан:
```json
{
  "ts": "2025-09-30T17:45:23.123Z",
  "level": "INFO",
  "app": "deep-calm",
  "svc": "dc-api",
  "env": "prod",
  "req_id": "abc123",
  "event": "campaign_created",
  "campaign_id": "uuid-001",
  "title": "Запуск сентябрь",
  "sku": "RELAX-60",
  "channels": ["vk", "direct"],
  "budget_rub": 15000
}
```

### Lead создан (с маскированным телефоном):
```json
{
  "ts": "2025-09-30T17:46:01.456Z",
  "level": "INFO",
  "event": "lead_created",
  "lead_id": "uuid-002",
  "phone": "+7999***4567",
  "utm_source": "vk",
  "utm_campaign": "Запуск сентябрь"
}
```

### Ошибка API:
```json
{
  "ts": "2025-09-30T17:47:12.789Z",
  "level": "ERROR",
  "event": "direct_api_call_failed",
  "method": "campaigns.add",
  "error": "Connection timeout",
  "error_type": "ConnectTimeout"
}
```

# DeepCalm — Инфраструктура (Логи, Тесты, Автодокументирование, Сквозная аналитика)

## 1. Система логирования (Production-ready)

### 1.1. Формат логов (JSON, structlog)

**Требования:**
- ✅ Все логи в JSON (одна строка = одно событие)
- ✅ PII-маскирование (телефоны, email)
- ✅ Correlation ID для трейсинга запросов
- ✅ Уровни: DEBUG (dev only), INFO (default), WARNING, ERROR, CRITICAL

**Стек:**
```python
# requirements.txt
structlog>=24.4.0
python-json-logger>=2.0.7
```

**Конфигурация (app/core/logging.py):**
```python
import structlog
import logging
from structlog.processors import JSONRenderer
import re

# PII-маскирование
def mask_pii(_, __, event_dict):
    """Маскирует телефоны и email в логах"""
    for key, value in event_dict.items():
        if isinstance(value, str):
            # Телефоны: +79991234567 → +7999***4567
            value = re.sub(r'(\+7\d{3})\d{3}(\d{4})', r'\1***\2', value)
            # Email: vasya@example.com → v***a@example.com
            value = re.sub(r'(\w)\w+(\w)@', r'\1***\2@', value)
            event_dict[key] = value
    return event_dict

def setup_logging(env: str):
    """Настройка structlog для production"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # correlation_id из контекста
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            mask_pii,  # PII-маскирование
            JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if env == "dev" else logging.INFO,
        handlers=[logging.StreamHandler()]
    )
```

**Использование в коде:**
```python
# app/api/v1/campaigns.py
import structlog
from contextvars import ContextVar

logger = structlog.get_logger(__name__)
correlation_id_var = ContextVar("correlation_id", default=None)

@app.middleware("http")
async def add_correlation_id(request, call_next):
    """Добавляет correlation_id в контекст каждого запроса"""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

@router.post("/campaigns")
async def create_campaign(campaign: CampaignCreate):
    logger.info(
        "campaign_create_started",
        campaign_title=campaign.title,
        sku=campaign.sku,
        channels=campaign.channels
    )

    try:
        # бизнес-логика
        result = await campaign_service.create(campaign)

        logger.info(
            "campaign_created",
            campaign_id=str(result.id),
            status="success"
        )
        return result

    except Exception as e:
        logger.error(
            "campaign_create_failed",
            error=str(e),
            exc_info=True  # добавит stack trace
        )
        raise
```

**Пример лога:**
```json
{
  "event": "campaign_created",
  "timestamp": "2025-09-30T14:23:45.123456Z",
  "level": "info",
  "logger": "app.api.v1.campaigns",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "campaign_id": "550e8400-e29b-41d4-a716-446655440001",
  "campaign_title": "Запуск сентябрь — Релакс",
  "sku": "RELAX-60",
  "channels": ["vk", "direct"],
  "status": "success"
}
```

**PII-маскирование в действии:**
```python
logger.info("lead_created", phone="+79991234567", email="vasya@example.com")
# Вывод: {"phone": "+7999***4567", "email": "v***a@example.com"}
```

---

## 2. Тестовая инфраструктура (TDD-ready)

### 2.1. Стек
```python
# requirements.txt (test dependencies)
pytest>=8.3.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
pytest-mock>=3.14.0
httpx>=0.27.0  # для TestClient (FastAPI)
faker>=28.0.0  # генерация тестовых данных
freezegun>=1.5.0  # мокирование времени
```

### 2.2. Структура тестов
```
tests/
  conftest.py                    # фикстуры
  fixtures/                      # seed data (JSON/YAML)
    campaigns.json
    spend_daily.json
    conversions.json
  unit/
    test_metrics.py              # TTP, CAC, ДРР расчёты
    test_pii_masking.py          # PII-маскирование
  integration/
    test_campaigns_api.py        # CRUD кампаний
    test_publishing_api.py       # публикация
    test_analytics_api.py        # аналитика
  contract/
    test_openapi_contract.py     # schemathesis
    test_event_schemas.py        # JSONSchema для EVENTS
  e2e/
    test_campaign_flow.py        # создание → публикация → статистика
  dq/
    test_marts_invariants.py     # DQ-проверки витрин
```

### 2.3. conftest.py (фикстуры)
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.core.config import settings
import json

# Test database
TEST_DB_URL = "postgresql://dc:dcpass@localhost:5432/dc_test"
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Создаёт тестовую БД перед запуском тестов"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Изолированная сессия БД для каждого теста"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(db_session):
    """FastAPI TestClient с test DB"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def seed_campaigns(db_session):
    """Загружает фейковые кампании из fixtures/campaigns.json"""
    with open("tests/fixtures/campaigns.json") as f:
        campaigns_data = json.load(f)

    for data in campaigns_data:
        campaign = Campaign(**data)
        db_session.add(campaign)
    db_session.commit()

@pytest.fixture
def mock_vk_api(mocker):
    """Мокирует VK Ads API"""
    return mocker.patch(
        "app.integrations.vk_ads.create_campaign",
        return_value={"external_campaign_id": "vk_mock_12345"}
    )
```

### 2.4. Примеры тестов

#### Unit-тест (метрики):
```python
# tests/unit/test_metrics.py
from datetime import datetime, timedelta
from app.services.metrics import calculate_cac, calculate_ttp

def test_cac_calculation():
    """CAC = spend / leads_paid"""
    assert calculate_cac(spend=5000, leads=10) == 500
    assert calculate_cac(spend=5000, leads=0) == 0  # деление на 0

def test_ttp_calculation():
    """TTP = дни от first_touch до purchase"""
    first_touch = datetime(2025, 9, 1, 10, 0, 0)
    purchase = datetime(2025, 9, 3, 14, 30, 0)

    assert calculate_ttp(first_touch, purchase) == 2  # 2 полных дня

    # Проверка: purchase_at >= first_touch_at
    with pytest.raises(ValueError, match="purchase_at must be >= first_touch_at"):
        calculate_ttp(purchase, first_touch)
```

#### Integration-тест (API):
```python
# tests/integration/test_campaigns_api.py
def test_create_campaign(client):
    """POST /api/v1/campaigns — создание кампании"""
    response = client.post("/api/v1/campaigns", json={
        "title": "Test Campaign",
        "sku": "RELAX-60",
        "budget_rub": 10000,
        "channels": ["vk", "direct"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Campaign"
    assert data["status"] == "draft"
    assert "id" in data

def test_get_campaigns(client, seed_campaigns):
    """GET /api/v1/campaigns — список кампаний"""
    response = client.get("/api/v1/campaigns")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # из fixtures/campaigns.json
    assert data[0]["title"] == "Запуск сентябрь — Релакс"
```

#### Contract-тест (OpenAPI):
```python
# tests/contract/test_openapi_contract.py
import schemathesis

schema = schemathesis.from_uri("http://localhost:8082/openapi.json")

@schema.parametrize()
def test_api_contract(case):
    """Все эндпоинты соответствуют OpenAPI схеме"""
    response = case.call()
    case.validate_response(response)
```

#### E2E-тест (полный флоу):
```python
# tests/e2e/test_campaign_flow.py
def test_campaign_full_flow(client, mock_vk_api, mock_direct_api):
    """E2E: создание → генерация креативов → публикация → проверка статистики"""

    # 1. Создание кампании
    campaign_resp = client.post("/api/v1/campaigns", json={
        "title": "E2E Test Campaign",
        "sku": "RELAX-60",
        "budget_rub": 5000,
        "channels": ["vk", "direct"]
    })
    campaign_id = campaign_resp.json()["id"]

    # 2. Генерация креативов
    creatives_resp = client.post("/api/v1/creatives/generate", json={
        "campaign_id": campaign_id,
        "count": 3
    })
    assert len(creatives_resp.json()) == 3

    # 3. Публикация
    publish_resp = client.post("/api/v1/publishing/publish", json={
        "campaign_id": campaign_id
    })
    assert publish_resp.status_code == 202
    assert mock_vk_api.called
    assert mock_direct_api.called

    # 4. Проверка статуса
    status_resp = client.get(f"/api/v1/publishing/status/{campaign_id}")
    assert status_resp.json()["status"] in ["publishing", "published"]
```

#### DQ-тест (Data Quality):
```python
# tests/dq/test_marts_invariants.py
def test_no_future_dates_in_marts(db_session):
    """Витрины не содержат дат из будущего"""
    from datetime import date
    today = date.today()

    future_rows = db_session.execute(
        "SELECT COUNT(*) FROM spend_daily WHERE date > :today",
        {"today": today}
    ).scalar()

    assert future_rows == 0, "Найдены записи с датами из будущего"

def test_no_duplicate_phones_in_leads(db_session):
    """Лиды не содержат дубликатов телефонов"""
    duplicates = db_session.execute("""
        SELECT phone, COUNT(*) as cnt
        FROM leads
        GROUP BY phone
        HAVING COUNT(*) > 1
    """).fetchall()

    assert len(duplicates) == 0, f"Найдены дубликаты: {duplicates}"

def test_utm_source_not_null_for_paid_leads(db_session):
    """Платные лиды имеют utm_source"""
    paid_without_utm = db_session.execute("""
        SELECT COUNT(*)
        FROM leads l
        JOIN conversions c ON c.lead_id = l.id
        WHERE l.utm_source IS NULL
    """).scalar()

    assert paid_without_utm == 0
```

### 2.5. Coverage Report
```bash
# Запуск с coverage
pytest --cov=app --cov-report=term --cov-report=html --cov-report=xml

# Целевые метрики:
# - Критичные модули (metrics, integrations, api): ≥85%
# - Остальные модули: ≥70%
```

**CI-гейт:** если coverage < 70% → блокировать merge.

---

## 3. Автодокументирование

### 3.1. OpenAPI (FastAPI встроенный)
```python
# app/main.py
app = FastAPI(
    title="DeepCalm API",
    version="0.1.0",
    description="Performance-маркетинг автопилот для массажного кабинета",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    openapi_url="/openapi.json"
)

# Автоматический экспорт в cortex/APIs/openapi.yaml
@app.on_event("startup")
async def export_openapi():
    """Экспортирует OpenAPI схему при старте приложения"""
    import json
    import yaml

    openapi_json = app.openapi()
    openapi_yaml = yaml.dump(openapi_json, default_flow_style=False)

    with open("/opt/deep-calm/cortex/APIs/openapi.yaml", "w") as f:
        f.write(openapi_yaml)

    logger.info("openapi_exported", path="/opt/deep-calm/cortex/APIs/openapi.yaml")
```

**Доступ к документации:**
- Swagger UI: `https://dev.dc.vasiliy-ivanov.ru/docs`
- ReDoc: `https://dev.dc.vasiliy-ivanov.ru/redoc`
- JSON: `https://dev.dc.vasiliy-ivanov.ru/openapi.json`

### 3.2. Docstrings (Google Style)
```python
# app/services/metrics.py
def calculate_cac(spend: float, leads: int) -> float:
    """
    Рассчитывает CAC (Customer Acquisition Cost).

    Args:
        spend: Расходы на рекламу (рубли)
        leads: Количество привлечённых лидов

    Returns:
        CAC в рублях (0 если leads = 0)

    Examples:
        >>> calculate_cac(5000, 10)
        500.0
        >>> calculate_cac(5000, 0)
        0.0

    Raises:
        ValueError: Если spend < 0 или leads < 0
    """
    if spend < 0 or leads < 0:
        raise ValueError("spend и leads должны быть >= 0")

    return spend / leads if leads > 0 else 0.0
```

### 3.3. Pydantic Schemas (auto-validation)
```python
# app/schemas/campaign.py
from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime

class CampaignCreate(BaseModel):
    """Схема создания кампании"""
    title: str = Field(..., min_length=3, max_length=255, description="Название кампании")
    sku: str = Field(..., pattern="^[A-Z-0-9]+$", description="SKU услуги (например, RELAX-60)")
    budget_rub: float = Field(..., gt=0, description="Бюджет в рублях")
    target_cac_rub: float = Field(500, description="Целевой CAC")
    target_drr: float = Field(0.20, ge=0, le=1, description="Целевой ДРР (0.20 = 20%)")
    channels: List[str] = Field(..., min_items=1, description="Площадки: vk, direct, avito")

    @validator("channels")
    def validate_channels(cls, v):
        allowed = {"vk", "direct", "avito"}
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"Недопустимые каналы: {invalid}. Разрешены: {allowed}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "Запуск сентябрь — Релакс",
                "sku": "RELAX-60",
                "budget_rub": 15000,
                "target_cac_rub": 450,
                "channels": ["vk", "direct"]
            }
        }
```

**Автоматическая документация в OpenAPI:**
- JSON Schema из Pydantic → OpenAPI `components.schemas`
- Примеры из `Config.schema_extra` → Swagger UI
- Валидация автоматическая (FastAPI + Pydantic)

### 3.4. Changelog & ADR
```markdown
# CHANGELOG.md (автоматическая генерация из коммитов)
## [0.2.0] - 2025-10-15
### Added
- Чат-боты (VK, Avito, Website) + AI-ассистент
- Fallback на владельца через Telegram
- Inbox для управления диалогами

### Changed
- Обновлён dashboard (добавлены sparklines)
- Улучшена сквозная аналитика (Identity Map)

### Fixed
- Исправлен баг с дублированием лидов по телефону

# cortex/ADR/ADR-DC-003-logging.md
# ADR-DC-003 — Логирование

**Контекст:** Нужна трейсабельность запросов для дебага production-инцидентов.

**Решение:** structlog + JSON + correlation_id + PII-маскирование.

**Альтернативы:** python-logging (отклонено: нет структурированных логов).

**Последствия:** +200ms на маскирование PII (приемлемо для INFO-level логов).
```

---

## 4. Сквозная аналитика (End-to-End Tracking)

### 4.1. Проблема attribution (атрибуция)
**Задача:** Связать клик по объявлению → запись в YCLIENTS → оплату → понять откуда клиент и сколько заплатили.

**Челленджи:**
1. **ITP/блокировщики** — Safari/Firefox блокируют 3rd-party cookies
2. **Кросс-девайс** — клиент кликнул на телефоне, записался с ПК
3. **YCLIENTS не хранит UTM** — нужно шить identity вручную

### 4.2. Identity Map (ключ: телефон)
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY,
  phone VARCHAR(20) UNIQUE NOT NULL,  -- +79991234567 (основной ключ)

  -- Первое касание (клик по объявлению)
  utm_source VARCHAR(50),       -- vk, direct, avito
  utm_campaign VARCHAR(100),    -- название кампании
  utm_content VARCHAR(100),     -- creative_id (для A/B тестов)
  utm_medium VARCHAR(50),       -- cpc, cpm
  utm_term VARCHAR(100),        -- ключевая фраза (Директ)

  -- Web ID (клиентский)
  web_id TEXT,                  -- localStorage UUID (fallback если cookies заблокированы)
  client_id TEXT,               -- Метрика ClientId

  -- YCLIENTS ID (после записи)
  yclients_id INT,              -- ID из YCLIENTS API

  -- Timestamps
  first_touch_at TIMESTAMPTZ,   -- первый клик
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Принцип работы:**
1. **Клик по объявлению** → лендинг с UTM-метками
2. **Лендинг (JS):**
   ```javascript
   // Сохраняем UTM в localStorage (fallback на cookies)
   const params = new URLSearchParams(window.location.search);
   const webId = localStorage.getItem('dc_web_id') || crypto.randomUUID();
   localStorage.setItem('dc_web_id', webId);

   localStorage.setItem('dc_utm', JSON.stringify({
     source: params.get('utm_source'),
     campaign: params.get('utm_campaign'),
     content: params.get('utm_content'),
     webId: webId
   }));
   ```
3. **Форма записи (сайт/бот):**
   ```python
   # Клиент вводит телефон +79991234567
   phone = normalize_phone(input_phone)  # +79991234567
   utm = get_utm_from_cookie_or_localstorage()  # достаём из cookies/localStorage

   # Ищем лида по телефону (или создаём нового)
   lead = db.query(Lead).filter_by(phone=phone).first()
   if not lead:
       lead = Lead(
           phone=phone,
           utm_source=utm['source'],
           utm_campaign=utm['campaign'],
           utm_content=utm['content'],
           web_id=utm['webId'],
           first_touch_at=datetime.now()
       )
       db.add(lead)
       db.commit()
   ```
4. **Запись в YCLIENTS:**
   ```python
   # После создания booking в YCLIENTS
   booking = yclients_api.create_booking(...)

   # Обновляем lead
   lead.yclients_id = booking['id']
   db.commit()
   ```
5. **Конверсия:**
   ```python
   # Когда клиент оплатил (YCLIENTS webhook: payment.captured)
   conversion = Conversion(
       lead_id=lead.id,
       campaign_id=get_campaign_by_title(lead.utm_campaign),
       channel_code=lead.utm_source,
       ttp_days=(payment.paid_at - lead.first_touch_at).days,
       revenue_rub=payment.amount,
       converted_at=payment.paid_at
   )
   db.add(conversion)
   db.commit()
   ```

### 4.3. UTM Tracking (детали)

**Структура UTM:**
```
https://landing.dc.vasiliy-ivanov.ru/?
  utm_source=vk                  # канал (vk, direct, avito)
  &utm_campaign=zapusk_sentyabr  # название кампании (slug)
  &utm_content=creative_a        # вариант креатива (A/B/C)
  &utm_medium=cpc                # модель оплаты
  &utm_term=massazh+relaks       # ключевая фраза (только Директ)
```

**Генерация UTM (автоматически при публикации):**
```python
# app/services/publishing.py
def generate_utm(campaign: Campaign, creative: Creative, channel: str) -> str:
    """Генерирует UTM-ссылку для креатива"""
    from urllib.parse import urlencode

    base_url = "https://landing.dc.vasiliy-ivanov.ru/"
    params = {
        "utm_source": channel,
        "utm_campaign": slugify(campaign.title),  # "zapusk-sentyabr-relaks"
        "utm_content": f"creative_{creative.variant.lower()}",  # "creative_a"
        "utm_medium": "cpc"
    }

    return f"{base_url}?{urlencode(params)}"
```

**Пример:**
```
Кампания: "Запуск сентябрь — Релакс"
Креатив: Вариант A
Канал: VK

→ https://landing.dc.vasiliy-ivanov.ru/?utm_source=vk&utm_campaign=zapusk-sentyabr-relaks&utm_content=creative_a&utm_medium=cpc
```

### 4.4. Яндекс.Метрика (оффлайн-конверсии)

**Задача:** Передать конверсии обратно в Метрику → Директ использует для автооптимизации.

**Nightly job:**
```python
# app/jobs/upload_offline_conversions.py
async def upload_offline_conversions_to_metrika():
    """Загружает вчерашние конверсии в Метрику"""
    from datetime import date, timedelta

    yesterday = date.today() - timedelta(days=1)

    # Выбираем конверсии за вчера
    conversions = db.query(Conversion).join(Lead).filter(
        func.date(Conversion.converted_at) == yesterday,
        Lead.client_id.isnot(None)  # есть ClientId из Метрики
    ).all()

    if not conversions:
        logger.info("no_conversions_to_upload", date=str(yesterday))
        return

    # Формируем CSV
    csv_data = "ClientId,Target,DateTime,Price,Currency\n"
    for conv in conversions:
        csv_data += f"{conv.lead.client_id},booking,{conv.converted_at.isoformat()},{conv.revenue_rub},RUB\n"

    # Загружаем в Метрику
    await yandex_metrika_api.upload_conversions(
        counter_id=settings.metrika_counter_id,
        csv_data=csv_data
    )

    logger.info(
        "offline_conversions_uploaded",
        count=len(conversions),
        date=str(yesterday)
    )
```

**Требования:**
- ClientId должен быть получен из Метрики (через JS на лендинге)
- Target = "booking" (создать цель в Метрике заранее)

**JS на лендинге (получение ClientId):**
```javascript
// После инициализации Метрики
ym(COUNTER_ID, 'getClientID', function(clientID) {
  // Отправляем ClientId на бэкенд при создании lead
  fetch('/api/v1/leads', {
    method: 'POST',
    body: JSON.stringify({
      phone: '+79991234567',
      utm: {...},
      client_id: clientID  // ClientId из Метрики
    })
  });
});
```

### 4.5. Коллтрекинг (опционально, Фаза 4+)

**Проблема:** Клиент звонит напрямую (не через сайт) → нет UTM-меток → не можем атрибутировать.

**Решение (Фаза 4):**
1. **Динамическая подмена номера** (Calltouch, Callibri, Mango Office)
   - Каждому визитору показываем уникальный номер
   - Привязываем номер к сессии (web_id + UTM)
   - Когда клиент звонит → коллтрекинг знает откуда он

2. **Статическая подмена** (MVP-вариант, бесплатно):
   - На VK объявлениях: +7 (999) 123-45-01
   - На Директе: +7 (999) 123-45-02
   - На Avito: +7 (999) 123-45-03
   - Разные номера → понятен источник

3. **IP-телефония с API** (Mango Office, Zadarma):
   ```python
   # Webhook от Mango: клиент позвонил на +7 (999) 123-45-01
   @app.post("/api/v1/webhooks/mango/call")
   async def mango_call_webhook(data: dict):
       phone = normalize_phone(data['from'])  # +79991234567
       called_number = data['to']  # +7 (999) 123-45-01

       # Определяем источник по номеру
       source_map = {
           "+79991234501": "vk",
           "+79991234502": "direct",
           "+79991234503": "avito"
       }
       utm_source = source_map.get(called_number, "unknown")

       # Создаём или обновляем lead
       lead = get_or_create_lead(phone, utm_source=utm_source)

       logger.info("call_received", phone=phone, source=utm_source)
   ```

**Для MVP:** Используем статическую подмену (3 номера на 3 площадки).

---

## 5. Дополнительные интеграции (Фаза 5)

### 5.1. Яндекс.Бизнес

**Статус API:** Официального API нет (по состоянию на 2025).

**Что можно:**
- Управление через веб-интерфейс (ручное)
- Ответы на отзывы вручную
- Отслеживание рейтинга вручную

**Заложено на будущее:**
```sql
-- Таблица для отзывов (если API появится)
CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  platform VARCHAR(20), -- yandex_maps, 2gis, google
  external_id TEXT UNIQUE,
  author_name TEXT,
  rating INT CHECK (rating BETWEEN 1 AND 5),
  text TEXT,
  response TEXT,  -- ответ владельца
  responded_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ
);
```

**LLM-автоответы (если API появится):**
```python
# Промпт для ответа на отзыв
prompt = f"""
Отзыв клиента (рейтинг {review.rating}/5):
"{review.text}"

Напиши ответ от владельца массажного кабинета DeepCalm.
Тон: {brandbook/tone.md}
- Если 5★ → поблагодари, пригласи ещё
- Если 1-2★ → извинись, предложи решение
- Если 3-4★ → поблагодари, спроси что улучшить
"""
response = await openai_api.generate(prompt)
```

### 5.2. 2GIS

**Статус API:** Places API доступен (платный, contact@2gis.ru).

**Что можно:**
- Размещение компании в каталоге (бесплатно, через форму)
- Обновление информации (телефон, адрес, часы работы)
- Получение отзывов (через API)

**Заложено на будущее:**
```python
# app/integrations/2gis.py
async def get_reviews(firm_id: str) -> List[dict]:
    """Получает отзывы из 2GIS"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://catalog.api.2gis.com/3.0/items?id={firm_id}",
            params={"key": settings.gis_api_key, "fields": "items.reviews"}
        )
        return resp.json()["result"]["items"][0]["reviews"]
```

### 5.3. VK Posts (публикация контента)

**API:** `wall.post` (VK API)

**Что можно:**
- Публикация постов на стену группы
- Фото/видео (не карусель! карусель только для рекламы)
- Отложенный постинг (publish_date)

**Реализация (Фаза 5):**
```python
# app/integrations/vk_posts.py
async def publish_post(
    token: str,
    group_id: int,
    message: str,
    attachments: List[str] = None,  # photo123_456, video123_456
    publish_date: datetime = None
):
    """Публикует пост на стену группы VK"""
    params = {
        "access_token": token,
        "v": "5.131",
        "owner_id": f"-{group_id}",  # отрицательный ID для группы
        "from_group": 1,
        "message": message
    }

    if attachments:
        params["attachments"] = ",".join(attachments)

    if publish_date:
        params["publish_date"] = int(publish_date.timestamp())

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.vk.com/method/wall.post",
            params=params
        )
        return resp.json()
```

**LLM-генерация постов:**
```python
# Промпт для контент-плана
prompt = f"""
Создай контент-план на неделю для VK группы массажного кабинета DeepCalm.

Форматы:
1. Польза (3 поста) — советы по релаксации, стресс-менеджменту
2. Социальное доказательство (2 поста) — отзывы клиентов, кейсы
3. Оффер (2 поста) — акции, скидки, новые услуги

Тон: {brandbook/tone.md}
Длина: до 500 символов на пост
Хэштеги: #массаж #релакс #москва
"""
posts = await openai_api.generate(prompt)

# Публикация с отложкой
for i, post in enumerate(posts):
    await vk_api.publish_post(
        message=post['text'],
        attachments=[post['image_url']],
        publish_date=datetime.now() + timedelta(days=i)
    )
```

**UI в админке (Фаза 5):**
```
┌─────────────────────────────────────────────────────────────┐
│ 📝 Контент-план VK                   [Сгенерировать AI]     │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 01.10.2025, 10:00 | Польза                              │ │
│ │ "5 способов снять стресс после рабочего дня..."         │ │
│ │ [Изображение: релакс-комната]                           │ │
│ │ [Редактировать] [Удалить] [Опубликовать сейчас]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 03.10.2025, 14:00 | Отзыв                               │ │
│ │ "Клиент Иван: 'Впервые попробовал глубокий массаж...'" │ │
│ │ [Изображение: фото кабинета]                            │ │
│ │ [Редактировать] [Отложить] [Отменить]                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Итоговая архитектура (все слои)

```
┌─────────────────────────────────────────────────────────────┐
│                    DeepCalm Architecture                     │
├─────────────────────────────────────────────────────────────┤
│ Admin UI (React + shadcn/ui)                                │
│   Dashboard | Campaigns | Creatives | Inbox | Media | Posts │
├─────────────────────────────────────────────────────────────┤
│ FastAPI Backend (Nexus)                                     │
│   /api/v1/campaigns  /creatives  /publishing  /analytics    │
│   /chatbot  /inbox  /integrations                           │
├─────────────────────────────────────────────────────────────┤
│ Services Layer                                               │
│   Metrics (CAC, TTP, ДРР) | Identity Map | LLM Creative Gen │
├─────────────────────────────────────────────────────────────┤
│ Integrations (коннекторы)                                   │
│   VK Ads | Директ | Avito | YCLIENTS | Метрика             │
│   VK Posts | VK Messages | Telegram Bots | Website Widget  │
│   Яндекс.Бизнес (future) | 2GIS (future)                   │
├─────────────────────────────────────────────────────────────┤
│ Data Layer (PostgreSQL 16)                                  │
│   campaigns | creatives | placements | leads | conversions  │
│   conversations | messages | bot_knowledge | reviews        │
│   mart_campaigns_daily (materialized view)                  │
├─────────────────────────────────────────────────────────────┤
│ Jobs (dc-jobs, cron)                                        │
│   sync_spend | sync_bookings | compute_marts               │
│   upload_offline_conversions | chatbot_processor           │
├─────────────────────────────────────────────────────────────┤
│ Observability (Aegis)                                       │
│   structlog (JSON) | Prometheus | Grafana | Alertmanager   │
│   Loki (log aggregation) | DQ checks                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Следующие шаги

1. **Запустить bootstrap** → базовая инфраструктура
2. **Запустить LLM essentials** → Python + FastAPI + DB
3. **Настроить логирование** → structlog + JSON + PII masking
4. **Написать первые тесты** → unit (metrics) + integration (campaigns API)
5. **Настроить сквозную аналитику** → Identity Map + UTM tracking
6. **Интегрировать Метрику** → оффлайн-конверсии (nightly job)

**Всё заложено, готово к реализации по фазам** 🚀
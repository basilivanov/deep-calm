# DeepCalm — Testing Standards

## Принципы

1. **TDD обязателен** — сначала тест (красный), потом код (зелёный), потом рефакторинг
2. **Coverage:** core функции ≥85%, остальное ≥70%
3. **Все тесты должны проходить** перед PR
4. **Изоляция:** каждый тест независим, можно запускать в любом порядке

## Типы тестов

### 1. Unit тесты (pytest)

Тестируем отдельные функции/классы без внешних зависимостей.

**Где:** `tests/unit/test_*.py`

**Пример:**
```python
# tests/unit/test_metrics.py
from app.core.metrics import calculate_cac

def test_calculate_cac_normal():
    """CAC = spend / leads"""
    cac = calculate_cac(spend=1000, leads=10)
    assert cac == 100.0

def test_calculate_cac_zero_leads():
    """CAC = 0 если нет лидов"""
    cac = calculate_cac(spend=1000, leads=0)
    assert cac == 0.0

def test_calculate_cac_negative_spend():
    """CAC не может быть отрицательным"""
    with pytest.raises(ValueError):
        calculate_cac(spend=-100, leads=10)
```

### 2. Integration тесты (pytest + БД)

Тестируем взаимодействие с БД, Redis, внешними API (с моками).

**Где:** `tests/integration/test_*.py`

**Пример:**
```python
# tests/integration/test_campaigns_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, db_session):
    """Создание кампании через API"""
    response = await client.post("/api/v1/campaigns", json={
        "title": "Test Campaign",
        "sku": "RELAX-60",
        "budget_rub": 5000,
        "channels": ["vk"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Campaign"
    assert data["status"] == "draft"

    # Проверяем что в БД создалось
    campaign = db_session.query(Campaign).filter_by(id=data["id"]).first()
    assert campaign is not None
    assert campaign.budget_rub == 5000
```

### 3. Contract тесты (schemathesis)

Тестируем соответствие API спецификации OpenAPI.

```bash
# Автоматически генерирует тесты из openapi.json
schemathesis run http://localhost:8000/openapi.json --checks all
```

**Проверяет:**
- Все эндпоинты возвращают правильные HTTP статусы
- Схемы ответов соответствуют OpenAPI
- Нет 500 ошибок

### 4. DQ тесты (data quality)

Тестируем качество данных в витринах.

**Где:** `tests/dq/test_*.py`

**Пример:**
```python
# tests/dq/test_marts_invariants.py
def test_no_future_dates(db_session):
    """В витринах нет дат из будущего"""
    from datetime import date

    result = db_session.execute("""
        SELECT COUNT(*) FROM mart_campaigns_daily
        WHERE date > CURRENT_DATE
    """).scalar()

    assert result == 0, "Найдены даты из будущего в mart_campaigns_daily"

def test_no_duplicate_phones(db_session):
    """Нет дубликатов телефонов в leads"""
    result = db_session.execute("""
        SELECT phone, COUNT(*) as cnt FROM leads
        GROUP BY phone HAVING COUNT(*) > 1
    """).fetchall()

    assert len(result) == 0, f"Найдены дубликаты телефонов: {result}"

def test_utm_not_null_for_paid_leads(db_session):
    """У платных лидов есть UTM"""
    result = db_session.execute("""
        SELECT COUNT(*) FROM leads
        WHERE utm_source IS NULL
        AND created_at > NOW() - INTERVAL '30 days'
    """).scalar()

    assert result == 0, "Найдены платные лиды без UTM"
```

### 5. E2E тесты (Playwright — опционально)

Тестируем UI + API end-to-end.

```typescript
// tests/e2e/test_dashboard.spec.ts
test('Dashboard показывает CAC график', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard');

  // Проверяем что график загрузился
  const chart = await page.locator('[data-testid="cac-chart"]');
  await expect(chart).toBeVisible();

  // Проверяем что есть данные
  const dataPoints = await page.locator('.recharts-line-dot').count();
  expect(dataPoints).toBeGreaterThan(0);
});
```

## Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app
from httpx import AsyncClient

# Test DB
TEST_DATABASE_URL = "postgresql://dc:dcpass@localhost:5432/dc_test"

@pytest.fixture(scope="session")
def engine():
    """SQLAlchemy engine для тестов"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine):
    """Изолированная сессия для каждого теста"""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
async def client(db_session):
    """HTTP клиент для тестирования API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def seed_campaigns(db_session):
    """Загружаем фейковые кампании из fixtures/campaigns.json"""
    with open("tests/fixtures/campaigns.json") as f:
        campaigns_data = json.load(f)

    for data in campaigns_data:
        campaign = Campaign(**data)
        db_session.add(campaign)

    db_session.commit()
    return campaigns_data
```

## Seed Data (фейковые данные)

Используем `faker` для генерации тестовых данных:

```python
# tests/utils/seed.py
from faker import Faker
from datetime import date, timedelta

fake = Faker("ru_RU")

def generate_campaign():
    return {
        "title": f"Тест {fake.word()}",
        "sku": fake.random_element(["RELAX-60", "DEEP-90"]),
        "budget_rub": fake.random_int(5000, 20000),
        "channels": fake.random_elements(["vk", "direct", "avito"], length=2, unique=True),
        "status": "active"
    }

def generate_lead():
    return {
        "phone": fake.phone_number(),
        "utm_source": fake.random_element(["vk", "direct", "avito"]),
        "utm_campaign": f"Тест {fake.word()}",
        "first_touch_at": fake.date_time_between(start_date="-30d", end_date="now")
    }
```

## Запуск тестов

```bash
# Все тесты
pytest

# Только unit
pytest tests/unit/

# С coverage
pytest --cov=app --cov-report=html

# Только изменённые файлы (быстро)
pytest --testmon

# Contract тесты
schemathesis run http://localhost:8000/openapi.json --checks all

# DQ тесты (nightly)
pytest tests/dq/ -v
```

## CI Pipeline

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml --cov-fail-under=70
    schemathesis run http://localhost:8000/openapi.json --checks all
```

## Правила

✅ **Всегда пиши тесты:**
- Новая функция → unit тест
- Новый API endpoint → integration тест
- Изменение витрины → DQ тест

❌ **Не делай:**
- Тесты зависимые друг от друга (порядок выполнения не важен)
- Тесты с реальными внешними API (моки обязательны)
- Commit без прохождения всех тестов

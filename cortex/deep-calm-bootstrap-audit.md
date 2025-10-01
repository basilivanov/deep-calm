# Аудит deep-calm-bootstrap.sh для LLM-driven MVP

## Общая оценка: 6.5/10

**Вердикт:** Скрипт хорош для ручного MVP, но **критически не готов** для автономной работы LLM-агентов.

---

## ❌ Критические пропуски для LLM-driven разработки

### 1. **Python Environment — отсутствует полностью**
LLM пишет Python-код, но окружение не подготовлено:

**Отсутствует:**
- ❌ Python 3.12+ установка
- ❌ venv/uv для изоляции зависимостей
- ❌ requirements.txt / pyproject.toml template
- ❌ pip/poetry/uv bootstrap
- ❌ Alembic для миграций БД
- ❌ pytest/coverage/black/ruff

**Последствие:** LLM не сможет запустить/протестировать код локально.

**Решение:**
```bash
# Добавить в bootstrap:
apt-get install -y python3.12 python3.12-venv python3-pip
python3.12 -m venv /opt/deep-calm/venv
source /opt/deep-calm/venv/bin/activate
pip install -U pip setuptools wheel

# Template requirements.txt
cat > /opt/deep-calm/requirements.txt <<EOF
fastapi[standard]>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
psycopg2-binary>=2.9.9
redis>=5.0.0
httpx>=0.27.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
black>=24.8.0
ruff>=0.6.0
EOF
pip install -r /opt/deep-calm/requirements.txt
```

---

### 2. **FastAPI Skeleton — нет базового приложения**
Docker Compose поднимает порты, но **нет кода**.

**Отсутствует:**
- ❌ `app/main.py` — FastAPI entrypoint
- ❌ `app/api/v1/` — роутеры
- ❌ `app/core/config.py` — настройки (Pydantic Settings)
- ❌ `app/db/session.py` — SQLAlchemy session
- ❌ `app/models/` — модели БД
- ❌ `app/schemas/` — Pydantic схемы
- ❌ `alembic/` — миграции

**Последствие:** LLM создаст код, но не будет куда его положить. Нет структуры.

**Решение:**
```bash
mkdir -p /opt/deep-calm/{app/{api/v1,core,db,models,schemas},tests,alembic/versions}

# app/main.py
cat > /opt/deep-calm/app/main.py <<'PY'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DeepCalm API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/v1/analytics/kpi")
async def get_kpi():
    return {"cac": 450, "drr": 0.18, "ttp_median": 7}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
PY

# app/core/config.py
cat > /opt/deep-calm/app/core/config.py <<'PY'
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DC_")

    env: str = "dev"
    db_url: str
    redis_url: str
    session_secret: str
    tg_bot_token: str = ""
    tg_chat_id: str = ""

settings = Settings()
PY
```

---

### 3. **Dockerfile для dc-api — отсутствует**
Compose использует заглушку `alpine:3.20 + nc`, но **нет образа приложения**.

**Отсутствует:**
- ❌ `Dockerfile` — multi-stage build
- ❌ `.dockerignore`
- ❌ Health check внутри контейнера

**Последствие:** LLM напишет код, но не сможет его задеплоить.

**Решение:**
```dockerfile
# /opt/deep-calm/Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY app/ /app/app/
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8080/healthz', timeout=3).raise_for_status()"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### 4. **Alembic Migrations — не настроены**
БД есть, но нет способа создавать таблицы.

**Отсутствует:**
- ❌ `alembic.ini`
- ❌ `alembic/env.py`
- ❌ Начальная миграция (create tables)

**Последствие:** LLM создаст модели, но таблицы не появятся в БД.

**Решение:**
```bash
cd /opt/deep-calm
alembic init alembic

# alembic.ini: sqlalchemy.url = postgresql://dc:dcpass@localhost:5432/dc_dev
# alembic/env.py: import app.models для автогенерации
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

---

### 5. **Логирование — нет структурированных логов**
Cortex требует JSON-логи, но настройка отсутствует.

**Отсутствует:**
- ❌ `app/core/logging.py` — structlog/python-json-logger
- ❌ Middleware для correlation_id
- ❌ PII-маскирование

**Последствие:** Логи неструктурированные, Aegis не сможет парсить.

**Решение:**
```python
# app/core/logging.py
import logging
import structlog

def setup_logging(env: str):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if env == "dev" else logging.INFO,
    )

# app/main.py: setup_logging(settings.env)
```

---

### 6. **Тестовая инфраструктура — отсутствует**
TDD требует тесты, но фреймворк не настроен.

**Отсутствует:**
- ❌ `conftest.py` — фикстуры pytest
- ❌ `tests/test_api.py` — примеры тестов
- ❌ `.coveragerc` — настройки coverage
- ❌ CI-команды для запуска тестов

**Последствие:** LLM напишет тесты, но не сможет их запустить.

**Решение:**
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    # TODO: test DB session
    pass

# tests/test_api.py
def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

# Команда: pytest --cov=app --cov-report=term --cov-report=html
```

---

### 7. **Мониторинг и метрики — не подключены**
Aegis требует метрики, но экспорт не настроен.

**Отсутствует:**
- ❌ Prometheus exporter (node_exporter, postgres_exporter)
- ❌ `/metrics` эндпоинт в FastAPI
- ❌ Grafana для дашбордов (опционально)

**Последствие:** Алерты Aegis не сработают, нет данных для DQ.

**Решение:**
```python
# requirements.txt: prometheus-client>=0.20.0
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

REQUEST_COUNT = Counter("dc_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_DURATION = Histogram("dc_request_duration_seconds", "Request duration", ["method", "endpoint"])

@app.middleware("http")
async def metrics_middleware(request, call_next):
    with REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

---

### 8. **CI/CD Pipeline — GitHub Actions отсутствует**
Cortex добавил `.github/workflows/docs-guard.yml`, но нет **теста кода**.

**Отсутствует:**
- ❌ `.github/workflows/test.yml` — запуск pytest
- ❌ `.github/workflows/lint.yml` — black/ruff
- ❌ `.github/workflows/build.yml` — сборка Docker
- ❌ Secrets для деплоя

**Последствие:** LLM закоммитит сломанный код, не заметив.

**Решение:**
```yaml
# .github/workflows/test.yml
name: test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: dc_test
          POSTGRES_USER: dc
          POSTGRES_PASSWORD: dcpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v4
```

---

### 9. **Hot Reload для разработки — не настроен**
LLM меняет код, но нужен рестарт контейнера.

**Отсутствует:**
- ❌ Volume mount для кода в dev
- ❌ `--reload` в uvicorn для dev

**Последствие:** Медленный feedback loop (30-60 сек на рестарт).

**Решение:**
```yaml
# docker-compose.yml (dev only)
dc-api:
  build: .
  volumes:
    - ./app:/app/app:ro
  command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
```

---

### 10. **LLM Context Injection — нет механизма**
LLM нужен способ читать текущее состояние проекта.

**Отсутствует:**
- ❌ `dc code-snapshot` — генерация дампа кода
- ❌ `dc diff-summary` — краткая сводка изменений
- ❌ Интеграция с `dc-context <task_id>`

**Последствие:** LLM будет переспрашивать "покажи код X".

**Решение:**
```bash
# /usr/local/bin/dc: добавить команды
snapshot)
  tree -I '__pycache__|*.pyc|.venv|pgdata|redisdata' /opt/deep-calm/app > /tmp/dc-snapshot.txt
  echo "Snapshot: /tmp/dc-snapshot.txt"
  ;;
diff)
  git diff HEAD~1..HEAD --stat
  ;;
```

---

### 11. **Pre-commit Hooks — нет валидации**
LLM может закоммитить невалидный код.

**Отсутствует:**
- ❌ `.pre-commit-config.yaml`
- ❌ Автоформатирование (black/ruff)
- ❌ Проверка секретов (gitleaks)

**Последствие:** CI упадёт после коммита, а не до.

**Решение:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

---

### 12. **Seed Data для тестов — нет fixtures**
TDD требует данные для тестов.

**Отсутствует:**
- ❌ `tests/fixtures/` — JSON/YAML с тестовыми данными
- ❌ `scripts/seed_db.py` — заполнение БД примерами

**Последствие:** LLM напишет тесты без данных → `AssertionError`.

**Решение:**
```python
# tests/fixtures/leads.json
[
  {"phone": "+79991234567", "utm_source": "vk", "utm_campaign": "calm_test", "created_at": "2025-09-01T10:00:00Z"},
  {"phone": "+79997654321", "utm_source": "direct", "utm_campaign": "promo_sep", "created_at": "2025-09-02T14:30:00Z"}
]

# conftest.py
@pytest.fixture
def seed_leads(db_session):
    import json
    with open("tests/fixtures/leads.json") as f:
        leads = json.load(f)
    for lead in leads:
        db_session.add(Lead(**lead))
    db_session.commit()
```

---

### 13. **OpenAPI Schema Validation — не автоматизирована**
Cortex требует обновлять `openapi.yaml`, но нет инструмента.

**Отсутствует:**
- ❌ Авто-экспорт OpenAPI из FastAPI: `app.openapi()` → `cortex/APIs/openapi.yaml`
- ❌ Schemathesis для contract-тестов

**Последствие:** LLM добавит эндпоинт, но забудет обновить документацию.

**Решение:**
```python
# scripts/export_openapi.py
import json
from app.main import app

with open("/opt/deep-calm/cortex/APIs/openapi.yaml", "w") as f:
    f.write(json.dumps(app.openapi(), indent=2))

# tests/test_contract.py
import schemathesis
schema = schemathesis.from_uri("http://localhost:8082/openapi.json")

@schema.parametrize()
def test_api_contract(case):
    case.call_and_validate()
```

---

### 14. **DB Migrations Guard — нет проверки применимости**
LLM создаст миграцию, но может сломать prod.

**Отсутствует:**
- ❌ `alembic check` — проверка pending migrations
- ❌ `alembic history` — лог изменений
- ❌ CI-гейт на `alembic upgrade --sql` (dry-run)

**Решение:**
```bash
# scripts/check_migrations.sh
alembic current
alembic check  # fail if pending
alembic upgrade --sql > /tmp/migration-preview.sql
echo "Preview: /tmp/migration-preview.sql"
```

---

### 15. **Task Workflow для LLM — не описан**
LLM не знает, как начать задачу.

**Отсутствует:**
- ❌ `TASKS/WORKFLOW.md` — пошаговый гайд для LLM
- ❌ Шаблон `TASKS/<id>/PLAN.md` — что делать

**Решение:**
```markdown
# TASKS/WORKFLOW.md
## Как LLM начинает задачу

1. Читай `cortex/AGENT_README.md` (Capsule)
2. Читай `TASKS/<id>/manifest.yaml` (контракт)
3. Генерируй `TASKS/<id>/PLAN.md`:
   - Что делать (acceptance-критерии)
   - Какие файлы менять
   - Какие тесты писать
4. Запускай `dc-context <id>` → получаешь Scoped Doc Pack
5. TDD: пиши тесты → код → зелёный → рефакторинг
6. Обнови доки (RUNBOOKS/ADR/APIs/EVENTS)
7. Создай `TASKS/<id>/DONE.md` — отчёт
8. Коммит: `git add . && git commit -m "feat(<id>): ..."` (conventional commits)
```

---

## ⚠️ Средние пропуски (желательно для production)

### 16. Rate Limiting на NGINX
**Риск:** Aegis не сможет отличить DDoS от легитимного трафика.

```nginx
# В NGX_DIR/dev.conf:
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
location /api/ {
  limit_req zone=api_limit burst=20 nodelay;
  ...
}
```

---

### 17. Redis Persistence Tuning
**Риск:** Потеря очередей при рестарте (до 60 сек данных).

```yaml
# redis: --save 30 10 --save 300 100 --appendonly yes --appendfsync everysec
```

---

### 18. Postgres Connection Pooling
**Риск:** Исчерпание соединений при нагрузке.

```python
# SQLAlchemy: pool_size=20, max_overflow=10, pool_pre_ping=True
```

---

### 19. CORS настройка для prod
**Риск:** Уязвимость XSS.

```python
# Убрать allow_origins=["*"], заменить на конкретные домены
```

---

### 20. Health Check Endpoint — расширенный
**Риск:** `/healthz` возвращает OK, но БД мертва.

```python
@app.get("/healthz")
async def healthz():
    # Проверить DB, Redis, S3
    return {"status": "ok", "db": "ok", "redis": "ok"}
```

---

## ✅ Что уже хорошо

1. **Разделение dev/test** — отличная практика
2. **Sudoers с NOPASSWD** — правильная автоматизация
3. **CLI `dc`** — удобный DevEx
4. **Бэкапы + rclone** — базовая надёжность
5. **Basic-auth на test** — простая защита
6. **NGINX + Let's Encrypt** — production-ready TLS
7. **UFW + fail2ban** — базовая безопасность
8. **Cortex + SSOT** — отличная база для docs-as-code

---

## Финальная таблица пропусков

| № | Категория | Критичность | Усилия | Последствие при отсутствии |
|---|-----------|-------------|--------|----------------------------|
| 1 | Python Environment | 🔴 CRITICAL | 30 мин | LLM не запустит код |
| 2 | FastAPI Skeleton | 🔴 CRITICAL | 1 час | LLM не поймёт структуру |
| 3 | Dockerfile | 🔴 CRITICAL | 20 мин | Нечего деплоить |
| 4 | Alembic Migrations | 🔴 CRITICAL | 30 мин | Таблицы не создадутся |
| 5 | Структурированные логи | 🔴 CRITICAL | 40 мин | Aegis слепой |
| 6 | Pytest Setup | 🔴 CRITICAL | 20 мин | TDD невозможен |
| 7 | Prometheus Metrics | 🟡 HIGH | 30 мин | Мониторинг слепой |
| 8 | CI/CD Pipeline | 🟡 HIGH | 1 час | Ломается prod |
| 9 | Hot Reload | 🟡 HIGH | 10 мин | Медленный feedback |
| 10 | Context Injection | 🟡 HIGH | 30 мин | LLM переспрашивает |
| 11 | Pre-commit Hooks | 🟢 MEDIUM | 15 мин | Грязные коммиты |
| 12 | Seed Data | 🟢 MEDIUM | 20 мин | Тесты без данных |
| 13 | OpenAPI Sync | 🟢 MEDIUM | 20 мин | Документация устареет |
| 14 | Migrations Guard | 🟢 MEDIUM | 15 мин | Сломанные миграции |
| 15 | Task Workflow | 🔴 CRITICAL | 30 мин | LLM не знает, с чего начать |

**Итого критичных пропусков:** 6
**Время на исправление критичных:** ~4 часа
**Общее время до production-ready:** ~8 часов

---

## Рекомендации по приоритету

### Сейчас (блокирует LLM-разработку):
1. Python Environment + requirements.txt
2. FastAPI Skeleton (app/main.py, app/core/, app/api/)
3. Dockerfile + docker-compose с mount volumes
4. Task Workflow для LLM (TASKS/WORKFLOW.md)
5. Pytest setup (conftest.py, test_api.py)

### В течение недели (критично для стабильности):
6. Alembic Migrations
7. Структурированные логи (structlog)
8. CI/CD Pipeline (GitHub Actions)
9. Prometheus Metrics
10. Hot Reload для dev

### Перед production (можно отложить для MVP):
11. Pre-commit Hooks
12. OpenAPI Sync автоматизация
13. Migrations Guard
14. Seed Data фикстуры
15. Rate Limiting + Redis tuning

---

## Выводы

**Скрипт отличный для ручного MVP**, но для LLM-driven разработки нужны:
- **Скелет приложения** (FastAPI + структура папок)
- **Окружение разработки** (Python + зависимости)
- **Инструменты для LLM** (context injection, workflow, hot reload)
- **CI-гейты** (тесты + линтеры + миграции)

**Время инвестиций:** 4-8 часов → получите **production-ready инфраструктуру** для автономной работы LLM.
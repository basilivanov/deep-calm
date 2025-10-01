# DeepCalm — Автопилот Performance-маркетинга

## Что уже готово ✅

### Документация
- ✅ **DEEP-CALM-MVP-BLUEPRINT.md** — полный чертёж системы (БД, API, UI, интеграции)
- ✅ **DEEP-CALM-ROADMAP.md** — дорожная карта (Фазы 1-5)
- ✅ **DEEP-CALM-INFRASTRUCTURE.md** — логи, тесты, документация, аналитика
- ✅ **DEEP-CALM-GITOPS.md** — CI/CD пайплайны
- ✅ **deep-calm-bootstrap.sh** — скрипт развёртывания инфраструктуры
- ✅ **deep-calm-bootstrap-audit.md** — аудит текущего состояния
- ✅ **deep-calm-cortex-additions.sh** — docs-as-code система

### Зависимости
- ✅ **requirements.txt** — 30+ Python пакетов (FastAPI, SQLAlchemy, OpenAI, pytest и др.)
- ✅ **package.json** — React + Vite + Radix UI + Recharts + shadcn/ui
- ✅ **.env.example** — все переменные окружения
- ✅ **Dockerfile** — multi-stage build для dc-api
- ✅ **alembic/** — структура для миграций БД

---

## Что нужно для старта 🚀

### 1. Базовая инфраструктура (запустить скрипт)

```bash
# Развернуть инфраструктуру (PostgreSQL, Redis, NGINX)
sudo bash deep-calm-bootstrap.sh

# Проверка
docker compose -f /opt/deep-calm/dev/docker-compose.yml ps
```

### 2. Python Backend (FastAPI)

**Нужно создать структуру:**
```
DeepCalm/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── logging.py          # structlog setup
│   │   └── db.py               # SQLAlchemy engine
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── campaign.py
│   │   ├── creative.py
│   │   ├── lead.py
│   │   ├── settings.py         # Phase 1.5
│   │   └── analyst_report.py   # Phase 1.5
│   ├── api/
│   │   └── v1/
│   │       ├── campaigns.py
│   │       ├── creatives.py
│   │       ├── publishing.py
│   │       ├── analytics.py
│   │       ├── settings.py     # Phase 1.5
│   │       └── analyst.py      # Phase 1.5
│   ├── integrations/
│   │   ├── vk_ads.py           # mock для MVP
│   │   ├── yandex_direct.py    # реальный API
│   │   ├── avito.py            # XML upload
│   │   ├── yclients.py
│   │   └── yandex_metrika.py
│   ├── analyst/                # Phase 1.5
│   │   └── agent.py            # AnalystAgent
│   ├── jobs/
│   │   ├── sync_spend.py
│   │   ├── sync_bookings.py
│   │   ├── compute_marts.py
│   │   └── analyst_weekly.py   # Phase 1.5
│   └── tests/
│       ├── conftest.py
│       ├── test_campaigns.py
│       └── fixtures/
│           ├── campaigns.json
│           └── spend_daily.json
```

**Команды:**
```bash
cd /opt/feature-factory/DeepCalm

# Создать venv
python3.12 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env
cp .env.example .env
# Отредактировать .env (вставить реальные токены)

# Создать первую миграцию
alembic revision --autogenerate -m "Initial schema"

# Применить миграции
alembic upgrade head

# Запустить dev-сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend (React + Vite)

**Нужно создать структуру:**
```
DeepCalm/
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── CampaignsList.tsx
│   │   │   ├── CampaignForm.tsx
│   │   │   ├── CreativesList.tsx
│   │   │   ├── SettingsPage.tsx     # Phase 1.5
│   │   │   └── AnalystPage.tsx      # Phase 1.5
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui компоненты
│   │   │   ├── CircularProgressBar.tsx
│   │   │   ├── RecommendationCard.tsx
│   │   │   └── ChatInterface.tsx    # для AI Аналитика
│   │   ├── api/
│   │   │   └── client.ts            # axios instance
│   │   └── hooks/
│   │       ├── useCampaigns.ts
│   │       ├── useSettings.ts       # Phase 1.5
│   │       └── useAnalyst.ts        # Phase 1.5
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
```

**Команды:**
```bash
cd /opt/feature-factory/DeepCalm

# Создать frontend проект
npm create vite@latest frontend -- --template react-ts
cd frontend

# Скопировать package.json
cp ../package.json .

# Установить зависимости
npm install

# Запустить dev-сервер
npm run dev
```

### 4. Миграции БД (Alembic)

**Создать начальную миграцию:**
```bash
alembic revision -m "Initial schema" --autogenerate
```

Файл создастся в `alembic/versions/xxxxx_initial_schema.py`

**Таблицы для создания:**
- channels
- campaigns
- creatives
- placements
- spend_daily
- leads
- bookings
- conversions
- settings (Phase 1.5)
- analyst_reports (Phase 1.5)

**Витрина:**
- mart_campaigns_daily (materialized view)

### 5. Токены интеграций (получить вручную)

**Обязательные для MVP:**
- ✅ OpenAI API Key — `https://platform.openai.com/api-keys`
- ✅ YCLIENTS Token — `https://yclients.com/settings/api`
- ✅ Яндекс.Метрика Token — OAuth через `https://oauth.yandex.ru`
- ✅ Telegram Bot Token — через @BotFather

**Опциональные (для Фазы 1):**
- Яндекс.Директ Token — OAuth
- Avito Client ID/Secret — через `https://developers.avito.ru`
- VK App ID — через `https://vk.com/apps?act=manage`

### 6. Seed Data (фейковые данные для тестов)

**Создать файлы:**
```bash
mkdir -p tests/fixtures

# tests/fixtures/campaigns.json (30 дней данных)
# tests/fixtures/spend_daily.json
# tests/fixtures/conversions.json
```

**Запустить seed:**
```bash
python -m app.cli seed --fixtures=tests/fixtures/
```

---

## Что НЕ нужно делать сейчас ❌

### Пропустить для MVP:
- ❌ Реальная генерация креативов через Vision AI (Фаза 3)
- ❌ VK Ads реальная интеграция (пока mock)
- ❌ Чат-боты (Фаза 2)
- ❌ WhatsApp Business (Фаза 2)
- ❌ Call tracking (Фаза 4)
- ❌ Яндекс.Бизнес / 2GIS (Фаза 5)

---

## Порядок разработки (для LLM)

### Этап 1: Backend Skeleton
1. Создать `app/main.py` (FastAPI app с CORS, healthcheck)
2. Создать `app/core/config.py` (Settings из .env)
3. Создать `app/core/db.py` (SQLAlchemy async engine)
4. Создать `app/core/logging.py` (structlog + PII masking)

### Этап 2: Models
1. Создать все SQLAlchemy модели в `app/models/`
2. Запустить `alembic revision --autogenerate`
3. Применить миграции `alembic upgrade head`

### Этап 3: API Endpoints
1. `app/api/v1/campaigns.py` — CRUD кампаний
2. `app/api/v1/creatives.py` — генерация креативов (mock)
3. `app/api/v1/publishing.py` — публикация на площадки
4. `app/api/v1/analytics.py` — dashboard данные

### Этап 4: Integrations (mock для MVP)
1. `app/integrations/vk_ads.py` — mock create_campaign
2. `app/integrations/yandex_direct.py` — реальный API
3. `app/integrations/avito.py` — XML upload
4. `app/integrations/yclients.py` — fetch bookings
5. `app/integrations/yandex_metrika.py` — upload conversions

### Этап 5: Frontend
1. Dashboard с графиками (CAC, Conv%, ДРР)
2. CampaignsList + CampaignForm
3. CreativesList
4. Интеграция с API (axios + react-query)

### Этап 6: Phase 1.5 (AI Аналитик)
1. `app/models/settings.py` + `app/models/analyst_report.py`
2. `app/api/v1/settings.py` — управление настройками
3. `app/api/v1/analyst.py` — AI агент
4. `app/analyst/agent.py` — AnalystAgent (GPT-4)
5. `app/jobs/analyst_weekly.py` — nightly job
6. Frontend: SettingsPage + AnalystPage

---

## Чек-лист запуска

- [ ] Bootstrap скрипт выполнен (`deep-calm-bootstrap.sh`)
- [ ] PostgreSQL доступен (`psql -h localhost -U dc -d deep_calm_dev`)
- [ ] Redis доступен (`redis-cli ping`)
- [ ] Python venv создан (`source venv/bin/activate`)
- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] `.env` настроен (скопирован из `.env.example`)
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] Backend запущен (`uvicorn app.main:app --reload`)
- [ ] Frontend запущен (`npm run dev`)
- [ ] Токены интеграций получены (OPENAI_API_KEY, YCLIENTS_TOKEN и др.)
- [ ] Seed data загружен (`python -m app.cli seed`)

---

## Помощь

**Документация:**
- Blueprint: `DEEP-CALM-MVP-BLUEPRINT.md` (полная спецификация)
- Roadmap: `DEEP-CALM-ROADMAP.md` (фазы разработки)
- Infrastructure: `DEEP-CALM-INFRASTRUCTURE.md` (логи, тесты, аналитика)
- GitOps: `DEEP-CALM-GITOPS.md` (CI/CD)

**Команды:**
```bash
# Проверка инфраструктуры
docker compose ps

# Логи
docker compose logs -f dc-api

# Пересборка образа
docker compose build dc-api

# Миграции
alembic current          # текущая версия
alembic history          # история миграций
alembic upgrade head     # применить все
alembic downgrade -1     # откатить последнюю

# Тесты
pytest --cov=app --cov-report=html

# Форматирование
black app/
ruff check app/
```
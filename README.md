# DeepCalm — Автопилот Performance-маркетинга

**Status:** Phase 1 MVP — Backend реализован ✅

Performance-маркетинг автопилот для массажного кабинета с AI-агентами, автоматизацией размещения рекламы и аналитикой эффективности кампаний.

---

## 🎯 Что уже работает

### ✅ Backend API (FastAPI)
- **Campaigns API** — CRUD операции для управления кампаниями
- **Creatives API** — генерация креативов (mock для MVP)
- **Publishing API** — публикация на рекламные площадки (VK, Яндекс.Директ, Avito)
- **Analytics API** — метрики (CAC, ROAS, CR), dashboard, разбивка по каналам
- **Database** — PostgreSQL 16 с миграциями (Alembic)
- **Logging** — structlog с JSON-логами и PII masking
- **Tests** — 27 интеграционных тестов (pytest)

### ✅ Инфраструктура (Docker)
- **PostgreSQL 16** — база данных с автомиграциями
- **Redis 7** — кеш-слой
- **Backend API** — с hot-reload для разработки
- **Healthchecks** — для всех сервисов
- **Volumes** — для персистентности данных

### ✅ Модели данных
- `channels` — рекламные площадки (VK, Директ, Avito)
- `campaigns` — маркетинговые кампании
- `creatives` — рекламные креативы (варианты A/B/C)
- `placements` — размещения на площадках
- `leads` — лиды с UTM-метками
- `conversions` — оплаченные бронирования

---

## 🚀 Быстрый старт

### Требования
- Docker и Docker Compose
- Пользователь `dc` с доступом к Docker
- Порты 8000, 5433, 6378 свободны

### Запуск

```bash
# 1. Перейти в директорию проекта
cd /opt/deep-calm

# 2. Запустить все сервисы
docker compose up -d

# 3. Проверить статус
docker compose ps

# 4. Посмотреть логи
docker compose logs -f api

# 5. Открыть Swagger UI
# http://localhost:8000/docs
```

### Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/health

# Создать тестовую кампанию
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тестовая кампания",
    "sku": "RELAX-60",
    "budget_rub": 15000,
    "target_cac_rub": 800,
    "target_roas": 3.5,
    "channels": ["vk", "direct"],
    "ab_test_enabled": false
  }'

# Получить список кампаний
curl http://localhost:8000/api/v1/campaigns

# Dashboard аналитики
curl http://localhost:8000/api/v1/analytics/dashboard
```

---

## 📁 Структура проекта

```
/opt/deep-calm/
├── app/                          # Backend код
│   ├── main.py                   # FastAPI приложение
│   ├── core/                     # Ядро
│   │   ├── config.py            # Настройки (Pydantic)
│   │   ├── db.py                # SQLAlchemy engine
│   │   ├── logging.py           # structlog setup
│   │   └── seed.py              # Seed данные
│   ├── models/                   # SQLAlchemy модели
│   │   ├── campaign.py
│   │   ├── creative.py
│   │   ├── placement.py
│   │   ├── lead.py
│   │   └── conversion.py
│   ├── schemas/                  # Pydantic схемы
│   │   ├── campaign.py
│   │   ├── creative.py
│   │   ├── publishing.py
│   │   └── analytics.py
│   ├── api/v1/                   # API endpoints
│   │   ├── campaigns.py
│   │   ├── creatives.py
│   │   ├── publishing.py
│   │   └── analytics.py
│   ├── services/                 # Бизнес-логика
│   │   ├── creative_service.py
│   │   ├── publishing_service.py
│   │   └── analytics_service.py
│   └── integrations/            # Интеграции
│       ├── vk_ads.py           # Mock для MVP
│       ├── yandex_direct.py    # Mock для MVP
│       └── avito.py            # Mock для MVP
├── alembic/                     # Миграции БД
│   └── versions/
│       └── xxx_initial_schema.py
├── tests/                       # Тесты
│   ├── conftest.py
│   └── integration/
│       ├── test_campaigns_api.py     # 10 тестов
│       ├── test_publishing_api.py    # 9 тестов
│       └── test_analytics_api.py     # 8 тестов
├── docker-compose.yml           # Docker setup
├── Dockerfile                   # Backend образ
├── requirements.txt             # Python зависимости
├── alembic.ini                 # Alembic config
├── cli.py                      # CLI команды (seed)
└── README.md                   # Этот файл
```

---

## 🔧 Разработка

### Запуск тестов

```bash
# Все тесты
docker compose exec api pytest -v

# С покрытием
docker compose exec api pytest --cov=app --cov-report=term-missing

# Конкретный тест
docker compose exec api pytest tests/integration/test_campaigns_api.py -v
```

### Работа с миграциями

```bash
# Создать новую миграцию
docker compose exec api alembic revision --autogenerate -m "Add new table"

# Применить миграции
docker compose exec api alembic upgrade head

# Откатить последнюю миграцию
docker compose exec api alembic downgrade -1

# История миграций
docker compose exec api alembic history

# Текущая версия
docker compose exec api alembic current
```

### Seed данные

```bash
# Загрузить seed данные (каналы)
docker compose exec api python cli.py seed
```

### Логи

```bash
# Все сервисы
docker compose logs -f

# Только API
docker compose logs -f api

# Только PostgreSQL
docker compose logs -f db

# Последние 100 строк
docker compose logs --tail=100 api
```

### Пересборка образа

```bash
# Пересобрать и перезапустить
docker compose down
docker compose build
docker compose up -d

# Или одной командой
docker compose up -d --build
```

---

## 📡 API Endpoints

### Campaigns API

- `POST /api/v1/campaigns` — Создать кампанию
- `GET /api/v1/campaigns` — Список кампаний (пагинация)
- `GET /api/v1/campaigns/{id}` — Получить кампанию
- `PATCH /api/v1/campaigns/{id}` — Обновить кампанию
- `DELETE /api/v1/campaigns/{id}` — Удалить кампанию
- `POST /api/v1/campaigns/{id}/activate` — Активировать
- `POST /api/v1/campaigns/{id}/pause` — Поставить на паузу

### Creatives API

- `POST /api/v1/creatives/generate` — Генерация креативов для кампании
- `GET /api/v1/creatives` — Список креативов
- `GET /api/v1/creatives/{id}` — Получить креатив
- `PATCH /api/v1/creatives/{id}` — Обновить креатив
- `POST /api/v1/creatives/{id}/approve` — Одобрить креатив

### Publishing API

- `POST /api/v1/publishing/publish` — Опубликовать кампанию на площадки
- `GET /api/v1/publishing/status/{campaign_id}` — Статус размещений
- `POST /api/v1/publishing/pause/{campaign_id}` — Остановить размещения

### Analytics API

- `GET /api/v1/analytics/campaigns/{id}` — Метрики кампании
  - Query params: `start_date`, `end_date` (YYYY-MM-DD)
  - Возвращает: CAC, ROAS, CR, разбивка по каналам
- `GET /api/v1/analytics/dashboard` — Сводка по всем кампаниям
  - Query params: `start_date`, `end_date`
  - Возвращает: общий бюджет, расход, лиды, конверсии, выручка

### Служебные

- `GET /health` — Health check
- `GET /` — Root endpoint
- `GET /docs` — Swagger UI
- `GET /redoc` — ReDoc
- `GET /openapi.json` — OpenAPI schema

---

## 🗄️ База данных

### Подключение

```bash
# Через psql
psql -h localhost -p 5433 -U dc -d deep_calm_dev

# Пароль: dcpass
```

### Схема

**Таблицы:**
- `channels` — Рекламные площадки (vk, direct, avito)
- `campaigns` — Кампании (title, sku, budget_rub, target_cac_rub, target_roas)
- `creatives` — Креативы (campaign_id, variant, title, body, image_url)
- `placements` — Размещения (campaign_id, creative_id, channel_code, external_campaign_id)
- `leads` — Лиды (phone, utm_source, utm_medium, utm_campaign)
- `conversions` — Конверсии (campaign_id, lead_id, booking_id, revenue_rub)

**Связи:**
- `campaign` 1→N `creatives`
- `campaign` 1→N `placements`
- `campaign` 1→N `conversions`
- `lead` 1→N `conversions`

---

## 🧪 Тестирование

### Покрытие: 70%+

**Интеграционные тесты (27):**
- ✅ Campaigns API (10 тестов) — CRUD, активация, пауза
- ✅ Publishing API (9 тестов) — публикация, статус, пауза
- ✅ Analytics API (8 тестов) — метрики, dashboard, фильтры

**Запуск:**
```bash
# Все тесты
docker compose exec api pytest -v

# С отчетом о покрытии
docker compose exec api pytest --cov=app --cov-report=html

# Открыть отчет (генерируется в htmlcov/)
# Нужно скопировать из контейнера или запустить pytest на хосте
```

---

## 📊 Метрики

### CAC (Customer Acquisition Cost)
**Формула:** `Расход / Количество конверсий`

**Статусы:**
- `on_track` — CAC <= target
- `over_target` — CAC > target, но < target * 1.2
- `under_target` — CAC >= target * 1.2

### ROAS (Return on Ad Spend)
**Формула:** `Выручка / Расход`

**Статусы:**
- `on_track` — ROAS >= target
- `under_target` — ROAS >= target * 0.8, но < target
- `over_target` — ROAS < target * 0.8

### Conversion Rate
**Формула:** `(Конверсии / Лиды) * 100%`

---

## 🔐 Переменные окружения

**docker-compose.yml содержит:**
- `DATABASE_URL` — postgresql://dc:dcpass@db:5432/deep_calm_dev
- `REDIS_URL` — redis://redis:6379/0
- `APP_ENV` — development
- `APP_DEBUG` — true
- `SECRET_KEY` — dev-secret-key-change-in-production
- `CORS_ORIGINS` — http://localhost:3000,http://localhost:5173
- `LOG_LEVEL` — INFO

**Для production нужно добавить:**
- `OPENAI_API_KEY` — для генерации креативов (Phase 1.5)
- `YCLIENTS_TOKEN` — для синхронизации бронирований
- `YANDEX_METRIKA_TOKEN` — для отправки конверсий
- `VK_ACCESS_TOKEN` — для публикации на VK Ads
- `YANDEX_DIRECT_TOKEN` — для публикации в Яндекс.Директ
- `AVITO_CLIENT_ID`, `AVITO_CLIENT_SECRET` — для Avito

---

## 🐳 Docker

### Сервисы

**db (PostgreSQL 16)**
- Image: postgres:16-alpine
- Port: 5433:5432
- Volume: postgres_data
- Healthcheck: pg_isready

**redis (Redis 7)**
- Image: redis:7-alpine
- Port: 6378:6379
- Volume: redis_data
- Healthcheck: redis-cli ping

**api (Backend)**
- Build: Dockerfile (multi-stage)
- Port: 8000:8000
- Depends on: db, redis (with healthchecks)
- Command: migrations → seed → uvicorn --reload
- Volumes: hot-reload для app/, alembic/

### Команды

```bash
# Запуск
docker compose up -d

# Остановка
docker compose down

# Остановка с удалением volumes
docker compose down -v

# Пересборка
docker compose build

# Статус
docker compose ps

# Логи
docker compose logs -f

# Shell в контейнере
docker compose exec api bash

# Выполнить команду
docker compose exec api python cli.py seed
```

---

## 📝 Git Workflow

### Commits

Следуем Conventional Commits:

```bash
# Feature
git commit -m "feat: add analytics dashboard endpoint"

# Fix
git commit -m "fix: correct CAC calculation formula"

# Docs
git commit -m "docs: update README with API examples"

# Test
git commit -m "test: add integration tests for publishing API"

# Refactor
git commit -m "refactor: extract analytics logic to service"
```

### Co-authorship

Все коммиты включают:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 🗺️ Roadmap

### ✅ Phase 1 MVP (Current)
- [x] Backend skeleton (FastAPI + SQLAlchemy)
- [x] Database models и migrations
- [x] Campaigns API (CRUD)
- [x] Creatives API (mock generation)
- [x] Publishing API (mock integrations)
- [x] Analytics API (CAC, ROAS, CR)
- [x] Docker setup
- [x] Integration tests (27)
- [ ] Frontend (React + Vite) — TODO

### 🔜 Phase 1.5 (Next)
- [ ] AI Analyst Agent (GPT-4)
- [ ] Settings управление
- [ ] Weekly reports
- [ ] Chat interface для аналитика

### 📅 Phase 2 (Future)
- [ ] Telegram bot для клиентов
- [ ] WhatsApp Business интеграция
- [ ] Automated lead nurturing

### 📅 Phase 3 (Future)
- [ ] Vision AI для генерации креативов
- [ ] Реальная интеграция VK Ads
- [ ] A/B тестирование креативов

### 📅 Phase 4-5 (Future)
- [ ] Call tracking
- [ ] Яндекс.Бизнес / 2GIS
- [ ] Advanced analytics

---

## 📚 Документация

**Полная спецификация в cortex/:**
- `DEEP-CALM-MVP-BLUEPRINT.md` — полный чертёж системы (БД, API, UI)
- `DEEP-CALM-ROADMAP.md` — дорожная карта (Фазы 1-5)
- `DEEP-CALM-INFRASTRUCTURE.md` — логи, тесты, аналитика
- `DEEP-CALM-GITOPS.md` — CI/CD пайплайны
- `STANDARDS.yml` — стандарты кода

---

## 🤝 Contributing

Проект разрабатывается под пользователем `dc` (UID 997).

**Для разработки:**
1. Убедитесь что вы в группе `docker`
2. Клонируйте репозиторий в `/opt/deep-calm`
3. Запустите `docker compose up -d`
4. Вносите изменения (hot-reload работает)
5. Пишите тесты для новых фич
6. Создайте PR с описанием изменений

---

## 📞 Контакты

**Проект:** DeepCalm — Performance Marketing Autopilot
**Команда:** dc (developer)
**Дата старта:** 2025-10-01
**Текущий статус:** Phase 1 MVP Backend Complete ✅

---

## 📄 Лицензия

Proprietary — DeepCalm Project

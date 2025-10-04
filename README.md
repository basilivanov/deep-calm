# DeepCalm — Автопилот Performance-маркетинга

**Status:** Phase 1 MVP — Backend + Frontend реализованы ✅

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

### ✅ Frontend (React + Vite)
- **Dashboard** — метрики кампаний (CAC, ROAS, CR, бюджет)
- **UI Kit** — Button, Card, MetricCard с DeepCalm брендбуком
- **Design System** — фирменные цвета (#F7F5F2, #6B4E3D, #A67C52)
- **Typography** — Inter (400, 600) из Google Fonts
- **React Query** — кеширование и автообновление данных (30 сек)
- **Recharts** — графики CAC и CR (в разработке)
- **Tests** — Vitest + Testing Library (Dashboard, AI Analyst, AI Chat)

### ✅ Инфраструктура (Docker)
- **PostgreSQL 16** — база данных (контейнер: `dc-dev-db`, internal)
- **Redis 7** — кеш-слой (контейнер: `dc-dev-redis`, internal)
- **Backend API** — FastAPI (контейнер: `dc-dev-api`, порт 127.0.0.1:**8000**)
- **Frontend (Admin)** — React+Vite (контейнер: `dc-dev-admin`, порт 127.0.0.1:**3000**)
- **Hot-reload** — работает для разработки
- **Volumes** — персистентные данные (pgdata, redisdata)

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
- Порты **3000** (admin) и **8000** (API) свободны на 127.0.0.1

### Запуск (DEV окружение)

```bash
# 1. Перейти в dev директорию
cd /opt/deep-calm/dev

# 2. Запустить все сервисы
docker compose up -d

# 3. Проверить статус
docker compose ps

# 4. Посмотреть логи
docker compose logs -f dc-api

# 5. Открыть приложение
# Frontend (Admin): http://127.0.0.1:8083
# Backend API (Swagger): http://127.0.0.1:8082/docs
```

### Проверка работоспособности

```bash
# Health check
curl http://127.0.0.1:8082/health

# Создать тестовую кампанию
curl -X POST http://127.0.0.1:8082/api/v1/campaigns \
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
curl http://127.0.0.1:8082/api/v1/campaigns

# Dashboard аналитики
curl http://127.0.0.1:8082/api/v1/analytics/dashboard
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
├── frontend/                    # Frontend код
│   ├── src/
│   │   ├── main.tsx            # React entry point
│   │   ├── App.tsx             # Main app component
│   │   ├── index.css           # Global styles (DeepCalm colors)
│   │   ├── api/
│   │   │   └── client.ts       # Axios API client
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Card.tsx    # Card component
│   │   │   │   └── Button.tsx  # Button component
│   │   │   └── MetricCard.tsx  # Metric display card
│   │   └── pages/
│   │       └── Dashboard.tsx   # Dashboard page
│   ├── index.html              # HTML template (Inter font)
│   ├── package.json            # Node dependencies
│   ├── vite.config.ts          # Vite config
│   ├── tailwind.config.js      # Tailwind (DeepCalm colors)
│   ├── tsconfig.json           # TypeScript config
│   └── Dockerfile              # Frontend образ
├── alembic/                     # Миграции БД
│   └── versions/
│       └── xxx_initial_schema.py
├── tests/                       # Тесты
│   ├── conftest.py
│   └── integration/
│       ├── test_campaigns_api.py     # 10 тестов
│       ├── test_publishing_api.py    # 9 тестов
│       └── test_analytics_api.py     # 8 тестов
├── cortex/                      # Документация
│   ├── DEEP-CALM-MVP-BLUEPRINT.md
│   ├── DEEP-CALM-ROADMAP.md
│   ├── DEEP-CALM-INFRASTRUCTURE.md
│   └── CHANGELOG.md            # История изменений
├── docker-compose.yml           # Docker setup (4 сервиса)
├── Dockerfile                   # Backend образ
├── requirements.txt             # Python зависимости
├── alembic.ini                 # Alembic config
├── cli.py                      # CLI команды (seed)
├── CLAUDE.md                   # Claude Code context
└── README.md                   # Этот файл
```

---

## 🔧 Разработка

### Запуск тестов

```bash
# Все тесты (из dev/)
cd /opt/deep-calm/dev
docker compose exec dc-api pytest -v

# С покрытием
docker compose exec dc-api pytest --cov=app --cov-report=term-missing

# Конкретный тест
docker compose exec dc-api pytest tests/integration/test_campaigns_api.py -v

# Frontend (Vitest)
cd /opt/deep-calm/frontend
npm run test

# Проверка: секреты Яндекс.Директа доступны в контейнере API
cd /opt/deep-calm/dev
docker compose exec dc-api env | grep DC_YANDEX_DIRECT

# Получить новый OAuth токен для Яндекс.Директа (sandbox)
cd /opt/deep-calm
./scripts/setup_yandex_direct_token.py   # можно оставить Client-Login пустым
```

> ⚙️  Фикстуры автоматически создают БД `dc_test` в контейнере `dc-dev-db`. Если хочется подключиться к другому инстансу Postgres, задай `TEST_DATABASE_URL` перед запуском pytest.

### Работа с миграциями

```bash
# Создать новую миграцию
docker compose exec dc-api alembic revision --autogenerate -m "Add new table"

# Применить миграции
docker compose exec dc-api alembic upgrade head

# Откатить последнюю миграцию
docker compose exec dc-api alembic downgrade -1

# История миграций
docker compose exec dc-api alembic history

# Текущая версия
docker compose exec dc-api alembic current
```

### Seed данные

```bash
# Загрузить seed данные (каналы)
docker compose exec dc-api python cli.py seed
```

### Логи

```bash
# Все сервисы (из dev/)
cd /opt/deep-calm/dev
docker compose logs -f

# Только API
docker compose logs -f dc-api

# Только PostgreSQL
docker compose logs -f dc-db

# Только Frontend
docker compose logs -f dc-admin

# Последние 100 строк
docker compose logs --tail=100 dc-api
```

### Пересборка образа

```bash
# Пересобрать образы (из корня проекта)
cd /opt/deep-calm
docker build -t deep-calm-api .
docker build -t deep-calm-frontend ./frontend

# Перезапустить (из dev/)
cd dev
docker compose down
docker compose up -d
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
# Через Docker (exec в контейнер)
docker exec -it dc-dev-db psql -U dc -d dc_dev

# Или напрямую, если порт пробро шен (по умолчанию НЕТ)
# psql -h localhost -p 5432 -U dc -d dc_dev

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

### Backend (pytest)
- Campaigns API — CRUD, активация, пауза
- Publishing API — публикация, статус, пауза
- Analytics API — метрики и фильтры
- Settings API — типы значений, фильтры, bulk‑апдейты

```bash
# Все тесты (из dev/)
cd /opt/deep-calm/dev
docker compose exec dc-api pytest -v

# С отчётом о покрытии
docker compose exec dc-api pytest --cov=app --cov-report=html

# Локально (без Docker)
PYTHONPATH=/opt/deep-calm venv/bin/pytest
```

### Frontend (Vitest)
- UI‑компоненты (MetricCard, Button, Card)
- Страница Dashboard — отображение данных сводки
- AIChat — приветствие, отправка сообщения

```bash
cd /opt/deep-calm/frontend
npm run test
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

**dev/docker-compose.yml содержит:**
- `DC_ENV` — dev
- `DC_DB_URL` — postgresql://dc:dcpass@dc-db:5432/dc_dev
- `DC_REDIS_URL` — redis://dc-redis:6379/0

**Для production нужно добавить:**
- `OPENAI_API_KEY` — для генерации креативов (Phase 1.5)
- `YCLIENTS_TOKEN` — для синхронизации бронирований
- `YANDEX_METRIKA_TOKEN` — для отправки конверсий
- `VK_ACCESS_TOKEN` — для публикации на VK Ads
- `YANDEX_DIRECT_TOKEN` — для публикации в Яндекс.Директ
- `AVITO_CLIENT_ID`, `AVITO_CLIENT_SECRET` — для Avito

---

## 🐳 Docker

### Сервисы (DEV окружение)

**dc-dev-db (PostgreSQL 16)**
- Container: `dc-dev-db`
- Image: postgres:16
- Port: internal only (внутри Docker сети)
- Volume: ./pgdata
- Database: dc_dev
- User: dc / dcpass

**dc-dev-redis (Redis 7)**
- Container: `dc-dev-redis`
- Image: redis:7
- Port: internal only
- Volume: ./redisdata
- Persistence: 60s/100 keys

**dc-dev-admin (Frontend)**
- Container: `dc-dev-admin`
- Image: deep-calm-frontend
- Port: **127.0.0.1:8083**:3000
- Environment: VITE_API_URL=http://dc-dev-api:8000
- Depends on: dc-api

**dc-dev-api (Backend)**
- Container: `dc-dev-api`
- Image: deep-calm-api
- Port: **127.0.0.1:8082**:8000
- Environment: DC_ENV=dev
- Depends on: dc-db, dc-redis
- Restart: unless-stopped

### Порты по окружениям

| Окружение | Frontend (в контейнере) | Backend API (в контейнере) | Примечание |
|-----------|-------------------------|-----------------------------|------------|
| dev       | 3000                    | 8000                        | Проброс на хост: `127.0.0.1:8083→3000`, `127.0.0.1:8082→8000` |
| test      | 3001                    | 8001                        | +1 к dev; пример: `127.0.0.1:8181→3001`, `127.0.0.1:8182→8001` |
| staging   | 3002                    | 8002                        | +2 к dev |
| prod      | nginx                   | nginx                       | Внешний доступ через 443/80 |

### Команды

```bash
# Запуск (из dev/)
cd /opt/deep-calm/dev
docker compose up -d

# Остановка
docker compose down

# Остановка с удалением volumes (ВНИМАНИЕ: удалит БД!)
docker compose down -v

# Статус
docker compose ps

# Логи
docker compose logs -f dc-api

# Shell в контейнере
docker exec -it dc-dev-api bash

# Выполнить команду
docker compose exec dc-api python cli.py seed

# Пересборка образов (из корня)
cd /opt/deep-calm
docker build -t deep-calm-api .
docker build -t deep-calm-frontend ./frontend
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
- [x] Docker setup (4 сервиса)
- [x] Integration tests (27)
- [x] Frontend (React + Vite + Tailwind)
- [x] Dashboard UI с DeepCalm брендбуком
- [x] React Query интеграция с Backend API

### 🔜 Phase 1.5 (Next)
- [ ] AI Analyst Agent (GPT-4)
- [ ] Settings управление
- [ ] Weekly reports
- [ ] Chat interface для аналитика

### 🔜 Phase 1.75 (Planned)
- [ ] Dev/Test hardening: `dc-dev-*` compose, Nginx, stop-кран maintenance, порты `8082/8083↔8000/3000`
- [ ] PR-пайплайн: lint/test, `openapi-diff`, автоматическое превью `pr-<id>.dev.dc...`
- [ ] Авто-миграции (`alembic upgrade head`), стоп-флаги `DEPLOY_ENABLED`/`DC_FREEZE`, cleanup превью

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

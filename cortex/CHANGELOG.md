# DeepCalm - Changelog

Все изменения проекта документируются в этом файле.

---

## [2025-10-01] Phase 1 MVP Complete ✅

### Added
- **Backend API (FastAPI)**
  - Campaigns API (CRUD, activation, pause)
  - Creatives API (mock generation для MVP)
  - Publishing API (mock integrations: VK, Яндекс.Директ, Avito)
  - Analytics API (CAC, ROAS, CR, dashboard, channel breakdown)
  - 27 integration tests (pytest)
  - PostgreSQL 16 с Alembic migrations
  - structlog с JSON-логами и PII masking

- **Frontend (React + Vite)**
  - Dashboard с метриками (CAC, ROAS, CR, бюджет, расход, лиды, конверсии)
  - UI Kit: Button, Card, MetricCard
  - DeepCalm брендбук применен ко всем компонентам
  - Цвета: #F7F5F2 (беж), #6B4E3D (коричневый), #A67C52 (акцент)
  - Typography: Inter (400, 600) из Google Fonts
  - React Query для кеширования (refetch каждые 30 сек)

- **Docker Infrastructure**
  - 4 контейнера: dc-dev-admin, dc-dev-api, dc-dev-db, dc-dev-redis
  - Naming convention: `dc-{env}-{service}`
  - Ports: 127.0.0.1:8083 (admin), 127.0.0.1:8082 (API)
  - PostgreSQL и Redis internal only (не пробрасываются)
  - Volumes: ./pgdata, ./redisdata

- **Documentation**
  - README.md - полный quick start guide
  - CLAUDE.md - context для Claude Code
  - cortex/CHANGELOG.md (этот файл)

### Changed
- **Переименование контейнеров** (было: deepcalm-*, стало: dc-dev-*)
  - deepcalm-frontend → **dc-dev-admin**
  - deepcalm-api → **dc-dev-api**
  - deepcalm-db → **dc-dev-db**
  - deepcalm-redis → **dc-dev-redis**

- **Порты** (было: localhost:5173/8000/5433/6378)
  - Frontend: localhost:5173 → **127.0.0.1:8083**
  - Backend: localhost:8000 → **127.0.0.1:8082**
  - PostgreSQL: 5433 → **internal only**
  - Redis: 6378 → **internal only**

- **База данных**
  - Name: deep_calm_dev → **dc_dev**
  - Connection: только внутри Docker сети

- **Docker Compose location**
  - Было: корень проекта (docker-compose.yml)
  - Стало: **dev/docker-compose.yml** (рабочий файл)

### NGINX Configuration

**DEV (dev.dc.vasiliy-ivanov.ru):**
- `/api/healthz` → 127.0.0.1:8082/health
- `/api/*` → 127.0.0.1:8082/ (Backend API)
- `/` → 127.0.0.1:8083 (Frontend)

**TEST (test.dc.vasiliy-ivanov.ru):**
- `/api/*` → 127.0.0.1:8182/ (Backend API)
- `/` → 127.0.0.1:8083 (Frontend) ⚠️ TODO: должно быть 8181

**Файлы:**
- `infra/nginx/dev.conf`
- `infra/nginx/test.conf`

### Technical Details

**Database Schema:**
- channels (vk, direct, avito)
- campaigns (title, sku, budget_rub, target_cac_rub, target_roas, status)
- creatives (campaign_id, variant, title, body, image_url, status)
- placements (campaign_id, creative_id, channel_code, external_campaign_id, status)
- leads (phone, utm_source, utm_medium, utm_campaign, landing_page_url)
- conversions (campaign_id, lead_id, booking_id, revenue_rub, booking_date)

**Environment Variables (dev):**
- DC_ENV=dev
- DC_DB_URL=postgresql://dc:dcpass@dc-db:5432/dc_dev
- DC_REDIS_URL=redis://dc-redis:6379/0

**Git Commits:**
- f264d2d: feat: Применение DeepCalm брендбука к Frontend UI
- 42984f9: feat: Frontend MVP (React + Vite + Tailwind + Dashboard)
- 139f2b5: feat: Docker setup и comprehensive README
- 97119b5: feat: Analytics API + seed data для channels
- 134ed04: feat: Publishing API + Creatives API + mock integrations

---

## [Next: Phase 1.5] Planned

### To Add
- AI Analyst Agent (GPT-4) для анализа кампаний
- Settings управление (user preferences)
- Weekly reports (автоматическая отправка)
- Chat interface для Analyst Agent

---

## Notes

### Container Naming Convention
Все контейнеры следуют формату: `dc-{environment}-{service}`

**Environments:**
- `dev` - разработка (127.0.0.1:808x)
- `test` - тестирование (127.0.0.1:818x)
- `prod` - продакшн (external domain)

**Services:**
- `admin` - Frontend (React)
- `api` - Backend (FastAPI)
- `db` - PostgreSQL
- `redis` - Redis

**Examples:**
- dc-dev-admin (development frontend)
- dc-test-api (testing backend)
- dc-prod-db (production database)

### Port Allocation
- **dev**: 808x (8082 API, 8083 admin)
- **test**: 818x (8182 API, 8181 admin)
- **prod**: 443/80 (nginx reverse proxy)

---

**Maintained by:** dc (DeepCalm developer)
**Last Updated:** 2025-10-01

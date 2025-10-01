# DeepCalm Project Context

## Session Continuity Information

**Current Status:** Initial infrastructure setup and planning phase

**Last Updated:** 2025-10-01

---

## Project Overview

**DeepCalm** - Performance Marketing Autopilot for Massage Salon
- **Tech Stack:** FastAPI (Python 3.12) + React (TypeScript) + PostgreSQL 16 + Redis
- **Development:** Docker-based with hot-reload
- **User:** dc (developer account)
- **Location:** /opt/deep-calm/

---

## Current Phase: Phase 1 MVP

**Goal:** Basic Publishing Automation

**What's Ready:**
- ✅ Documentation (180KB specs in cortex/)
- ✅ Bootstrap script (creates infrastructure)
- ✅ Docker configs (docker-compose.dev.yml)
- ✅ Implementation plan (IMPLEMENTATION-PLAN.md - 5 days)
- ✅ Pre-start checklist (PRE-START-CHECKLIST.md)
- ✅ User setup guide (SETUP-FOR-DC-USER.md)

**What's Next:**
1. Run bootstrap script (creates /opt/deep-calm/)
2. Configure dc user (shell, password, git)
3. Start Day 1: Backend Skeleton
   - app/main.py (FastAPI)
   - app/core/ (config, db, logging)
   - app/models/ (SQLAlchemy)
   - Alembic migrations

---

## Important Files

### Documentation (Read First)
- `/opt/deep-calm/cortex/DEEP-CALM-MVP-BLUEPRINT.md` - Full system spec (41KB)
- `/opt/deep-calm/cortex/DEEP-CALM-ROADMAP.md` - 5 phases (47KB)
- `/opt/deep-calm/cortex/DEEP-CALM-INFRASTRUCTURE.md` - Logs, tests, analytics (37KB)
- `/opt/deep-calm/IMPLEMENTATION-PLAN.md` - Day-by-day plan

### Key Configs
- `dev/docker-compose.yml` - Development Docker setup (РАБОЧИЙ)
- `docker-compose.yml` - Устаревший, используется `dev/`
- `requirements.txt` - Python dependencies (30+ packages)
- `frontend/package.json` - React dependencies

---

## Development Workflow

### User: dc
```bash
whoami  # dc
cd /opt/deep-calm/dev  # ⚠️ Работаем из dev/
```

### Docker Commands
```bash
# Start all services (из dev/)
cd /opt/deep-calm/dev
docker compose up -d

# Logs
docker compose logs -f dc-api

# Shell in container
docker exec -it dc-dev-api bash

# Migrations
docker compose exec dc-api alembic upgrade head
```

### Ports (DEV)
- Frontend (Admin): http://127.0.0.1:**8083**
- Backend API: http://127.0.0.1:**8082**
- PostgreSQL: internal only (dc-dev-db)
- Redis: internal only (dc-dev-redis)

### Container Names (стиль: dc-{env}-{service})
- `dc-dev-admin` - Frontend
- `dc-dev-api` - Backend API
- `dc-dev-db` - PostgreSQL 16
- `dc-dev-redis` - Redis 7

---

## Database Schema (Key Tables)

From DEEP-CALM-MVP-BLUEPRINT.md:
- `channels` - Ad platforms (VK, Директ, Avito)
- `campaigns` - Marketing campaigns
- `creatives` - Ad creatives (variants A/B/C)
- `placements` - Published ads
- `leads` - Customer leads (phone, UTM)
- `conversions` - Paid bookings
- `settings` - User preferences (Phase 1.5)
- `analyst_reports` - AI reports (Phase 1.5)

---

## Integrations (Phase 1)

### Mock (for MVP)
- VK Ads - no public API, using mock

### Real
- Яндекс.Директ - API v5
- Avito - XML autoload API
- YCLIENTS - REST API (bookings)
- Яндекс.Метрика - offline conversions

**Use WebFetch to get API docs when needed!**

---

## Key Decisions (Architecture)

1. **Sync SQLAlchemy** (not async) - simpler for MVP
2. **APScheduler** (not Celery) - nightly jobs sufficient
3. **Docker development** - all services in containers
4. **User dc** - development under dc user
5. **Hot-reload** - volume mounts for backend/frontend

---

## Git Configuration

```bash
# For dc user
git config --global user.name "DeepCalm Developer"
git config --global user.email "dc@deepcalm.local"
```

**Commit format:**
```
feat: description

Detailed changes

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Testing Strategy

- Coverage target: ≥70%
- Types: Unit, Integration, Contract (schemathesis), DQ, E2E
- Run: `cd /opt/deep-calm/dev && docker compose exec dc-api pytest --cov=app`

---

## Important Notes

### Security
- Never commit .env files
- Use .gitignore.template (includes secrets!)
- PII masking in logs (phones, emails)

### Database
- PostgreSQL: internal only (не пробрасывается наружу в dev)
- DB Name: `dc_dev` (не deep_calm_dev!)
- Backup: `docker exec dc-dev-db pg_dump -U dc dc_dev > backup.sql`

### Development
- Hot-reload: НЕТ в dev (образы пересобираются)
- Для hot-reload нужны volume mounts (не настроены в dev/docker-compose.yml)
- Для изменений: пересобрать образ + restart container

---

## Current Task Status

**Phase:** Phase 1 MVP Complete ✅

**Completed:**
1. Backend API (FastAPI + PostgreSQL + Redis)
2. Frontend (React + Vite + Tailwind + DeepCalm брендбук)
3. Docker setup (4 контейнера: dc-dev-{admin,api,db,redis})
4. 27 integration tests
5. Documentation (README, CLAUDE.md, cortex/)

**Current:**
- Обновление документации с актуальными портами и названиями контейнеров
- Фиксация стиля именования: `dc-{env}-{service}`

**Next:**
- Phase 1.5: AI Analyst Agent

---

## Session Continuation Notes

**To resume this project after logout:**
```bash
# Login as dc
su - dc

# Navigate to project
cd /opt/deep-calm

# Resume Claude session
claude --resume
# (or claude --continue for most recent)

# This CLAUDE.md file will be automatically loaded!
```

**Context preserved in:**
- This CLAUDE.md file (project memory)
- Git history (when initialized)
- Documentation in cortex/ (always available)
- IMPLEMENTATION-PLAN.md (day-by-day tasks)

---

## Quick Reference

**Key Commands:**
```bash
# User
whoami                    # should be: dc
groups                    # should include: docker

# Project
cd /opt/deep-calm/dev    # ⚠️ dev окружение

# Docker (из dev/)
docker compose ps                    # status
docker compose up -d                 # start
docker compose logs -f dc-api        # logs API
docker compose logs -f dc-admin      # logs Frontend
docker compose exec dc-api bash      # shell в API
docker exec -it dc-dev-db psql -U dc dc_dev  # PostgreSQL

# Containers
docker ps  # показывает: dc-dev-admin, dc-dev-api, dc-dev-db, dc-dev-redis

# Образы (пересборка из корня)
cd /opt/deep-calm
docker build -t deep-calm-api .
docker build -t deep-calm-frontend ./frontend

# Git
git status
git log --oneline

# Documentation
cat cortex/DEEP-CALM-MVP-BLUEPRINT.md  # main spec
cat README.md                           # quick start
```

---

**URLs (DEV):**
- Frontend: http://127.0.0.1:8083
- Backend API: http://127.0.0.1:8082/docs

**Last Session:** Phase 1 MVP completed + documentation update
**Status:** Production-ready MVP ✅

*This file is automatically read by Claude Code at session start*

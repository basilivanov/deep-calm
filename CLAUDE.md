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
- `docker-compose.dev.yml` - Development Docker setup
- `.gitignore.template` - Comprehensive gitignore (224 lines)
- `requirements.txt` - Python dependencies (30+ packages)
- `package.json` - React dependencies

---

## Development Workflow

### User: dc
```bash
whoami  # dc
cd /opt/deep-calm
```

### Docker Commands
```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d

# Logs
docker compose -f docker-compose.dev.yml logs -f dc-api

# Shell in container
docker compose -f docker-compose.dev.yml exec dc-api bash

# Migrations
docker compose -f docker-compose.dev.yml exec dc-api alembic upgrade head
```

### Ports
- Backend API: http://localhost:8084
- Frontend: http://localhost:8083
- PostgreSQL: localhost:5432 (dc/dcpass/deep_calm_dev)
- Redis: localhost:6379

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
- Run: `docker compose -f docker-compose.dev.yml exec dc-api pytest --cov=app`

---

## Important Notes

### Security
- Never commit .env files
- Use .gitignore.template (includes secrets!)
- PII masking in logs (phones, emails)

### Database
- PostgreSQL volumes: 999:999 ownership (Docker user)
- Backup before migrations: `pg_dump > backups/backup_$(date +%Y%m%d).sql`

### Development
- Hot-reload works for both backend and frontend
- Changes in app/ → backend restarts automatically
- Changes in frontend/src/ → HMR in browser

---

## Current Task Status

**Phase:** Pre-deployment (setting up environment)

**Last Actions:**
1. Created comprehensive documentation
2. Prepared Docker configs
3. Created user setup guides
4. Ready to run bootstrap script

**Next Actions:**
1. Run bootstrap: `sudo bash deep-calm-bootstrap.sh`
2. Setup dc user: shell, password, groups
3. Initialize git repository
4. Start Day 1: Backend Skeleton

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
groups                    # should include: dcops, docker

# Project
cd /opt/deep-calm
ls -la                    # check ownership (dc:dcops)

# Docker
docker compose -f docker-compose.dev.yml ps     # status
docker compose -f docker-compose.dev.yml up -d  # start
docker compose -f docker-compose.dev.yml logs -f dc-api  # logs

# Git
git status
git log --oneline

# Documentation
cat cortex/DEEP-CALM-MVP-BLUEPRINT.md  # main spec
cat IMPLEMENTATION-PLAN.md              # day-by-day plan
```

---

**Last Session:** Initial planning and setup
**Ready for:** Bootstrap deployment and Phase 1 development

*This file is automatically read by Claude Code at session start*

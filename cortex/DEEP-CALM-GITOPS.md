# DeepCalm GitOps — Continuous Deployment

## Принципы

1. **Git = Source of Truth** — весь код, конфиги, инфраструктура в Git
2. **Automated Pipelines** — push в `main` → автодеплой в `test`, tag → деплой в `prod`
3. **Immutable Artifacts** — Docker images с тегами (sha256)
4. **Declarative Config** — docker-compose.yml, .env templates в репо
5. **Observability** — логи деплоя, rollback одной кнопкой

---

## Архитектура GitOps

```
┌─────────────────────────────────────────────────────────────┐
│ GitHub Repository: deep-calm                                 │
├─────────────────────────────────────────────────────────────┤
│ main branch                                                  │
│   ├── app/                 (FastAPI backend)                │
│   ├── app/ui/              (React frontend)                 │
│   ├── cortex/             (Docs-as-code)                    │
│   ├── tests/              (pytest)                          │
│   ├── docker-compose.yml  (dev/test/prod configs)          │
│   ├── Dockerfile          (multi-stage build)              │
│   ├── .github/workflows/  (CI/CD pipelines)                │
│   └── ansible/            (deployment playbooks)           │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ (git push / PR merge)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ GitHub Actions (CI/CD)                                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Lint & Test (pytest, black, ruff)                       │
│ 2. Build Docker Image (tag: sha-abc123)                    │
│ 3. Push to GHCR (ghcr.io/vasiliy-ivanov/deep-calm)        │
│ 4. Deploy to Dev (SSH → docker compose pull && up -d)      │
│ 5. Deploy to Test (on tag push)                            │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ (SSH deploy)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Server: vasiliy-ivanov.ru                                   │
├─────────────────────────────────────────────────────────────┤
│ /opt/deep-calm/dev/   (docker-compose up, auto-pull)       │
│ /opt/deep-calm/test/  (docker-compose up, manual trigger)  │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Repository Structure

```
deep-calm/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Lint + Test (каждый push)
│   │   ├── build-push.yml      # Build Docker → GHCR
│   │   ├── deploy-dev.yml      # Деплой в dev (auto)
│   │   └── deploy-test.yml     # Деплой в test (manual)
│   ├── CODEOWNERS              # Василий = owner всего
│   └── dependabot.yml          # Авто-обновление зависимостей
│
├── app/                        # FastAPI backend
├── app/ui/                     # React frontend
├── tests/                      # pytest tests
├── cortex/                     # Docs-as-code
│
├── ansible/
│   ├── deploy.yml              # Playbook деплоя
│   ├── rollback.yml            # Playbook отката
│   └── inventory.ini           # dev/test серверы
│
├── docker-compose.yml          # Base compose (переменные из .env)
├── docker-compose.dev.yml      # Dev overrides
├── docker-compose.test.yml     # Test overrides
│
├── Dockerfile                  # Multi-stage build
├── .dockerignore               # Исключения
├── requirements.txt            # Python deps
├── pyproject.toml              # Poetry config
│
├── .env.example                # Template для .env
├── README.md                   # Setup instructions
└── CHANGELOG.md                # Auto-generated from commits
```

---

## GitHub Actions Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Триггер:** каждый push, PR

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install black ruff

      - name: Lint Python
        run: |
          black --check app/
          ruff check app/

      - name: Lint UI
        working-directory: app/ui
        run: |
          npm install
          npm run lint

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
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://dc:dcpass@localhost:5432/dc_test
        run: |
          alembic upgrade head

      - name: Run tests
        env:
          DATABASE_URL: postgresql://dc:dcpass@localhost:5432/dc_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

  ui-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install UI dependencies
        working-directory: app/ui
        run: npm ci

      - name: Run UI tests
        working-directory: app/ui
        run: npm test -- --coverage

      - name: Build UI
        working-directory: app/ui
        run: npm run build
```

---

### 2. Build & Push (`.github/workflows/build-push.yml`)

**Триггер:** push в `main`, создание tag

```yaml
name: Build & Push

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### 3. Deploy to Dev (`.github/workflows/deploy-dev.yml`)

**Триггер:** push в `main` (после успешного build)

```yaml
name: Deploy to Dev

on:
  workflow_run:
    workflows: ["Build & Push"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Dev
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.DEV_HOST }}
          username: ${{ secrets.DEV_USER }}
          key: ${{ secrets.DEV_SSH_KEY }}
          script: |
            cd /opt/deep-calm/dev
            docker compose pull dc-api
            docker compose up -d dc-api
            docker compose ps

      - name: Health check
        run: |
          sleep 10
          curl -f https://dev.dc.vasiliy-ivanov.ru/healthz || exit 1

      - name: Notify Telegram
        if: always()
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          message: |
            🚀 Deploy to Dev: ${{ job.status }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
            URL: https://dev.dc.vasiliy-ivanov.ru
```

---

### 4. Deploy to Test (`.github/workflows/deploy-test.yml`)

**Триггер:** manual (workflow_dispatch) или tag push

```yaml
name: Deploy to Test

on:
  workflow_dispatch:
    inputs:
      tag:
        description: 'Docker image tag to deploy'
        required: true
        default: 'main'

  push:
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: test  # GitHub Environment (требует approval)

    steps:
      - uses: actions/checkout@v4

      - name: Determine tag
        id: tag
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "tag=${{ github.event.inputs.tag }}" >> $GITHUB_OUTPUT
          else
            echo "tag=${GITHUB_REF##*/}" >> $GITHUB_OUTPUT
          fi

      - name: Deploy to Test
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.TEST_HOST }}
          username: ${{ secrets.TEST_USER }}
          key: ${{ secrets.TEST_SSH_KEY }}
          script: |
            cd /opt/deep-calm/test
            export IMAGE_TAG=${{ steps.tag.outputs.tag }}
            docker compose pull dc-api
            docker compose up -d dc-api
            docker compose ps

      - name: Health check
        run: |
          sleep 10
          curl -f -u ops:${{ secrets.TEST_BASIC_AUTH_PASS }} https://test.dc.vasiliy-ivanov.ru/healthz || exit 1

      - name: Run smoke tests
        run: |
          pytest tests/e2e/smoke/ --base-url https://test.dc.vasiliy-ivanov.ru

      - name: Notify Telegram
        if: always()
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          message: |
            🎯 Deploy to Test: ${{ job.status }}
            Tag: ${{ steps.tag.outputs.tag }}
            URL: https://test.dc.vasiliy-ivanov.ru
```

---

## Ansible Playbooks (опционально)

Если SSH-действия станут сложными, переходим на Ansible.

### `ansible/deploy.yml`
```yaml
---
- name: Deploy DeepCalm
  hosts: "{{ env }}"
  vars:
    project_root: "/opt/deep-calm/{{ env }}"
    image_tag: "{{ tag | default('main') }}"

  tasks:
    - name: Pull latest code
      git:
        repo: https://github.com/vasiliy-ivanov/deep-calm.git
        dest: "{{ project_root }}"
        version: "{{ image_tag }}"
      become: yes
      become_user: dc

    - name: Pull Docker images
      docker_compose:
        project_src: "{{ project_root }}"
        pull: yes
      become: yes

    - name: Start services
      docker_compose:
        project_src: "{{ project_root }}"
        state: present
        restarted: yes
      become: yes

    - name: Wait for healthz
      uri:
        url: "https://{{ env }}.dc.vasiliy-ivanov.ru/healthz"
        status_code: 200
      retries: 10
      delay: 5

    - name: Log deployment
      shell: |
        echo "$(date) - Deployed {{ image_tag }} to {{ env }}" >> {{ project_root }}/deploy.log
```

**Запуск:**
```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml -e "env=dev tag=main"
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml -e "env=test tag=v0.2.0"
```

---

## Secrets Management

### GitHub Environments
**Settings → Environments → New environment**

#### Environment: `dev`
**Secrets:**
- `DEV_HOST` = `vasiliy-ivanov.ru`
- `DEV_USER` = `dc`
- `DEV_SSH_KEY` = (private SSH key)
- `TELEGRAM_CHAT_ID` = `833478509`
- `TELEGRAM_BOT_TOKEN` = `...`

#### Environment: `test`
**Secrets:**
- `TEST_HOST` = `vasiliy-ivanov.ru`
- `TEST_USER` = `dc`
- `TEST_SSH_KEY` = (private SSH key)
- `TEST_BASIC_AUTH_PASS` = `ops123`
- Остальные как в `dev`

**Protection rules:**
- `test` environment: требует approval (можно настроить)
- `prod` (будущее): обязательный approval + ограничение по ветке

---

## Rollback Strategy

### 1. Автоматический rollback (при health check failure)
```yaml
# В deploy workflow добавить:
- name: Rollback on failure
  if: failure()
  uses: appleboy/ssh-action@v1.0.0
  with:
    host: ${{ secrets.DEV_HOST }}
    username: ${{ secrets.DEV_USER }}
    key: ${{ secrets.DEV_SSH_KEY }}
    script: |
      cd /opt/deep-calm/dev
      docker compose down dc-api
      docker compose pull dc-api:previous  # предыдущий тег
      docker compose up -d dc-api
```

### 2. Ручной rollback через GitHub Actions
**Workflow dispatch:**
```yaml
# .github/workflows/rollback.yml
name: Rollback

on:
  workflow_dispatch:
    inputs:
      env:
        description: 'Environment (dev/test)'
        required: true
        type: choice
        options:
          - dev
          - test
      tag:
        description: 'Tag to rollback to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    steps:
      - name: Rollback
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets[format('{0}_HOST', inputs.env)] }}
          username: ${{ secrets[format('{0}_USER', inputs.env)] }}
          key: ${{ secrets[format('{0}_SSH_KEY', inputs.env)] }}
          script: |
            cd /opt/deep-calm/${{ inputs.env }}
            export IMAGE_TAG=${{ inputs.tag }}
            docker compose pull dc-api
            docker compose up -d dc-api
```

**Использование:**
1. GitHub → Actions → Rollback → Run workflow
2. Выбрать `env=dev`, `tag=sha-abc123`
3. Подтвердить

### 3. Tag-based versioning (лучшая практика)
```bash
# При релизе создаём тег
git tag -a v0.2.0 -m "Release 0.2.0: Added chatbots"
git push origin v0.2.0

# Docker image: ghcr.io/vasiliy-ivanov/deep-calm:v0.2.0

# Откат на предыдущую версию
export IMAGE_TAG=v0.1.9
docker compose pull && docker compose up -d
```

---

## Observability (деплой-метрики)

### 1. Deployment logs в БД
```sql
CREATE TABLE deployments (
  id SERIAL PRIMARY KEY,
  env VARCHAR(10), -- dev|test|prod
  tag VARCHAR(50), -- git commit sha или version tag
  status VARCHAR(20), -- success|failed|rolled_back
  deployed_by VARCHAR(100), -- GitHub actor
  deployed_at TIMESTAMPTZ DEFAULT NOW(),
  rollback_from VARCHAR(50), -- предыдущий tag (если rollback)
  logs TEXT
);
```

**Запись в CI:**
```yaml
- name: Log deployment
  run: |
    psql $DATABASE_URL -c "
      INSERT INTO deployments (env, tag, status, deployed_by)
      VALUES ('dev', '${{ github.sha }}', 'success', '${{ github.actor }}');
    "
```

### 2. Grafana Dashboard (деплой-частота)
```promql
# Количество деплоев в день
rate(deployments_total[1d])

# MTTR (Mean Time To Recovery)
avg(deployment_duration_seconds{status="success"})

# Failure rate
sum(deployments_total{status="failed"}) / sum(deployments_total)
```

---

## Dependabot (автообновление зависимостей)

### `.github/dependabot.yml`
```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"

  # npm (UI)
  - package-ecosystem: "npm"
    directory: "/app/ui"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "ui"

  # Docker base images
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "ci"
```

**Результат:** автоматические PR с обновлениями зависимостей (CI проверяет автоматически).

---

## Database Migrations (GitOps для схемы БД)

### Alembic (версионирование схемы)
```bash
# Создание миграции
alembic revision --autogenerate -m "Add conversations table"

# Применение в CI/CD
alembic upgrade head
```

**В CI pipeline:**
```yaml
- name: Run migrations
  run: |
    alembic upgrade head
```

**Откат миграции (при rollback):**
```bash
# В rollback playbook
alembic downgrade -1  # откат на 1 миграцию назад
```

**Best practice:** миграции backward-compatible (можно откатить без потери данных).

---

## LLM-Friendly GitOps

### 1. Автокоммиты от LLM
```bash
# LLM создаёт код → коммитит → пушит
git add .
git commit -m "feat(campaigns): add CAC calculation to dashboard

- Added calculate_cac() function
- Updated Dashboard.tsx with CAC sparkline
- Tests: test_cac_calculation.py

🤖 Generated with Claude Code"

git push origin main
```

**CI автоматически:**
1. Запускает тесты
2. Если зелёные → деплоит в dev
3. Уведомляет в Telegram

### 2. PR-based workflow (опционально для production)
```bash
# LLM создаёт ветку
git checkout -b feat/chatbot-inbox
# ... делает изменения ...
git push origin feat/chatbot-inbox

# LLM создаёт PR через GitHub CLI
gh pr create --title "feat: Add chatbot inbox" --body "..."
```

**Ты ревьюишь PR** → merge → автодеплой.

---

## Мониторинг GitOps (Telegram-уведомления)

### Формат уведомлений
```
🚀 Deploy to Dev: success
Commit: abc1234 (feat: add CAC sparkline)
Author: claude-code-bot
Duration: 2m 34s
URL: https://dev.dc.vasiliy-ivanov.ru

✅ Health check passed
✅ Tests passed (127/127)
📊 Coverage: 82%
```

**При ошибке:**
```
❌ Deploy to Dev: failed
Commit: def5678 (fix: update metrics)
Error: Health check failed (500 Internal Server Error)

🔄 Auto-rollback: reverted to abc1234
URL: https://dev.dc.vasiliy-ivanov.ru

Logs: https://github.com/.../actions/runs/123456
```

---

## Итоговый GitOps Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LLM пишет код → коммит в main                            │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. GitHub Actions: CI (lint + test)                         │
│    ✅ Все тесты зелёные → продолжаем                         │
│    ❌ Тесты падают → блокируем деплой + уведомление          │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Build Docker Image → Push to GHCR                        │
│    Tag: ghcr.io/vasiliy-ivanov/deep-calm:sha-abc123         │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Deploy to Dev (auto)                                     │
│    SSH → docker compose pull && up -d                       │
│    Health check → ✅ 200 OK                                  │
│    Telegram: "🚀 Deploy success"                            │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. (Manual) Deploy to Test                                  │
│    GitHub Actions → Run workflow → Select tag               │
│    SSH → docker compose pull && up -d                       │
│    Smoke tests → ✅ Passed                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Следующие шаги

1. **Создать GitHub репо:** `vasiliy-ivanov/deep-calm`
2. **Добавить Secrets** в Settings → Secrets and variables → Actions
3. **Сгенерировать SSH ключи:**
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/deep-calm-deploy -C "github-actions"
   # Публичный ключ → сервер: ~/.ssh/authorized_keys
   # Приватный ключ → GitHub Secrets: DEV_SSH_KEY
   ```
4. **Создать workflows:** скопировать `.github/workflows/*.yml` в репо
5. **Первый коммит:**
   ```bash
   git init
   git add .
   git commit -m "feat: initial deep-calm setup"
   git remote add origin git@github.com:vasiliy-ivanov/deep-calm.git
   git push -u origin main
   ```
6. **Проверить CI:** GitHub → Actions → должны запуститься workflows

---

**GitOps готов!** Теперь каждый push в `main` → автодеплой в dev. Rollback одной кнопкой. 🚀
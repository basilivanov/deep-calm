# DeepCalm — Documentation Standards

## Принципы

1. **Docs-as-code** — документация в Git, версионируется как код
2. **Single Source of Truth** — один источник правды (Cortex)
3. **Актуальность** — документация обновляется вместе с кодом
4. **Для LLM** — документы должны быть читаемы агентами

## Структура Cortex

```
cortex/
├── DEEP-CALM-MVP-BLUEPRINT.md      # Чертёж системы (SSOT)
├── DEEP-CALM-ROADMAP.md            # Дорожная карта
├── DEEP-CALM-INFRASTRUCTURE.md     # Инфраструктура
├── DEEP-CALM-GITOPS.md             # CI/CD
├── AGENT_README.md                 # Точка входа для LLM
├── STANDARDS.yml                   # Стандарты (обязательны)
├── METRICS_DICTIONARY.md           # Определения метрик
├── APIs/
│   └── openapi.yaml                # OpenAPI спецификация (авто-генерится)
├── EVENTS/
│   ├── lead_created.schema.json    # JSON Schema событий
│   └── conversion_tracked.schema.json
├── policies/
│   ├── aegis_alerts.yml            # Правила алертов
│   └── bidder_rules.yml            # Правила биддера
├── TESTPLAN.md                     # План тестирования
├── ADR/                            # Architecture Decision Records
│   └── ADR-001-database-choice.md
├── RUNBOOKS/                       # Операционные инструкции
│   ├── incident-api-down.md
│   └── rollback-deployment.md
├── brandbook/
│   └── creative_rules.md           # Правила креативов
├── GUIDES/
│   ├── LOGGING.md
│   ├── TESTING.md
│   ├── CODE_STYLE.md
│   ├── DOCUMENTATION.md (этот файл)
│   ├── NGINX.md
│   └── CI.md
├── Security/
│   ├── SECURITY.md
│   └── RELEASE_CHECKLIST.md
└── Templates/
    ├── PR_TEMPLATE.md
    ├── ISSUE_TEMPLATE.md
    ├── POSTMORTEM.md
    └── ADR_TEMPLATE.md
```

## Когда обновлять документацию

### Обязательно обновить ПЕРЕД PR:

1. **Изменил API?** → обнови `APIs/openapi.yaml` (автогенерация через FastAPI)
2. **Добавил событие?** → создай схему в `EVENTS/*.schema.json`
3. **Изменил метрику?** → обнови `METRICS_DICTIONARY.md`
4. **Новое архитектурное решение?** → создай ADR в `ADR/ADR-XXX.md`
5. **Новая интеграция?** → обнови `DEEP-CALM-MVP-BLUEPRINT.md` секцию "Интеграции"
6. **Изменил БД?** → обнови `DEEP-CALM-MVP-BLUEPRINT.md` секцию "Схема БД"

### Не обязательно (но желательно):

- Bugfix → упомяни в commit message (не нужно ADR)
- Рефакторинг → если меняется архитектура → ADR
- Новый тест → не нужно документировать отдельно

## OpenAPI (автогенерация)

FastAPI автоматически генерирует OpenAPI из кода:

```python
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

app = FastAPI(
    title="DeepCalm API",
    version="0.1.0",
    description="Performance Marketing Automation"
)

class CampaignCreate(BaseModel):
    """Создание кампании"""
    title: str
    sku: str
    budget_rub: float
    channels: List[str]

@app.post("/api/v1/campaigns", response_model=CampaignResponse)
async def create_campaign(data: CampaignCreate):
    """Создать кампанию

    - **title**: Название кампании
    - **sku**: SKU услуги (RELAX-60, DEEP-90 и т.д.)
    - **budget_rub**: Бюджет в рублях
    - **channels**: Список каналов (vk, direct, avito)
    """
    ...
```

Доступно на `/docs` (Swagger UI) и `/openapi.json`.

Сохраняй в Cortex:
```bash
curl http://localhost:8000/openapi.json > cortex/APIs/openapi.yaml
```

## ADR (Architecture Decision Records)

Формат:
```markdown
# ADR-DC-001 — Выбор PostgreSQL вместо MongoDB

**Статус:** Принято
**Дата:** 2025-09-30
**Автор:** Василий

## Контекст
Нужна БД для хранения кампаний, лидов, конверсий. Требуется поддержка транзакций и сложных JOIN для витрин.

## Решение
Используем PostgreSQL 16.

## Последствия
- ✅ Полная поддержка SQL, транзакции ACID
- ✅ Materialized views для витрин
- ✅ JSON поддержка (JSONB) для гибкости
- ❌ Сложнее горизонтальное масштабирование (но для MVP не критично)

## Альтернативы
- MongoDB — нет JOIN, сложнее агрегации
- MySQL — менее богатый SQL, хуже JSON поддержка
```

## RUNBOOKS (Операционные инструкции)

Формат:
```markdown
# RUNBOOK: API недоступен (5xx errors)

## Симптомы
- `/healthz` возвращает 500 или timeout
- В логах: `database_connection_lost`

## Диагностика
1. Проверь контейнеры:
   ```bash
   dc --env prod ps
   ```

2. Проверь логи API:
   ```bash
   dc --env prod logs dc-api --tail 100
   ```

3. Проверь БД:
   ```bash
   psql -h localhost -U dc -d dc_prod -c "SELECT 1;"
   ```

## Исправление
Если БД недоступна:
```bash
dc --env prod restart dc-db
dc --env prod restart dc-api
```

Если не помогло → откат на предыдущую версию:
```bash
dc --env prod rollback
```

## Эскалация
Если проблема не решена за 15 минут → пиши в Telegram: @vasily_ivanov
```

## Markdown Style

### Заголовки
```markdown
# H1 — только для названия документа
## H2 — основные разделы
### H3 — подразделы
#### H4 — редко (только если нужна глубокая вложенность)
```

### Код
````markdown
```python
# Всегда указывай язык
def foo():
    pass
```
````

### Списки
```markdown
- Ненумерованные списки — тире
- Не звёздочки

1. Нумерованные списки
2. Начинай с 1
```

### Таблицы
```markdown
| Колонка 1 | Колонка 2 | Колонка 3 |
|-----------|-----------|-----------|
| Значение  | Значение  | Значение  |
```

### Ссылки
```markdown
[Текст ссылки](https://example.com)

Относительные ссылки внутри Cortex:
[STANDARDS](STANDARDS.yml)
[Blueprint](DEEP-CALM-MVP-BLUEPRINT.md)
```

## Проверка документации

CI проверяет:
1. Все `.md` файлы проходят `markdownlint`
2. Внутренние ссылки не битые (dead links)
3. Обязательные документы присутствуют (Blueprint, Roadmap, Standards)

```bash
# Локально
markdownlint cortex/*.md
```

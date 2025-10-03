# DeepCalm — Code Style

## Python (Backend)

### Форматирование
- **black** — автоформатирование (line-length=100)
- **ruff** — линтер (заменяет flake8 + isort + pylint)
- **mypy** — type checking

```bash
# Форматирование
black app/

# Линтинг
ruff check app/

# Type checking
mypy app/
```

### Именование
- **Файлы:** `snake_case.py`
- **Классы:** `PascalCase`
- **Функции/переменные:** `snake_case`
- **Константы:** `UPPER_SNAKE_CASE`
- **Private:** `_leading_underscore`

```python
# ✅ Хорошо
class CampaignService:
    def create_campaign(self, title: str, budget_rub: float) -> Campaign:
        MAX_BUDGET = 100000
        ...

# ❌ Плохо
class campaign_service:
    def CreateCampaign(self, Title: str, budgetRub: float):
        maxBudget = 100000
```

### Type Hints (обязательно!)

```python
from typing import Optional, List
from datetime import date

# ✅ Всегда указывай типы
async def fetch_campaigns(
    status: str,
    date_from: Optional[date] = None,
    channels: List[str] = []
) -> List[Campaign]:
    ...

# ❌ Без типов — запрещено
async def fetch_campaigns(status, date_from=None, channels=[]):
    ...
```

### Docstrings (Google style)

```python
def calculate_cac(spend: float, leads: int) -> float:
    """Рассчитывает CAC (Customer Acquisition Cost).

    Args:
        spend: Потраченная сумма в рублях
        leads: Количество лидов

    Returns:
        CAC в рублях. Возвращает 0 если leads == 0.

    Raises:
        ValueError: Если spend отрицательный

    Example:
        >>> calculate_cac(1000, 10)
        100.0
    """
    if spend < 0:
        raise ValueError("spend не может быть отрицательным")

    return spend / leads if leads > 0 else 0.0
```

### Структура файла

```python
"""Модуль для работы с кампаниями.

Содержит CRUD операции, бизнес-логику и валидацию.
"""

# 1. Стандартная библиотека
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

# 2. Сторонние библиотеки
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 3. Локальные импорты
from app.core.db import get_session
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignResponse

# 4. Код
router = APIRouter()

@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(...):
    ...
```

## TypeScript (Frontend)

### Форматирование
- **Prettier** + **ESLint**
- Tabs → 2 spaces
- Single quotes
- Semicolons — yes

```typescript
// ✅ Хорошо
const fetchCampaigns = async (): Promise<Campaign[]> => {
  const response = await api.get('/campaigns');
  return response.data;
};

// ❌ Плохо (без типов, двойные кавычки, нет semicolon)
const fetchCampaigns = async () => {
  const response = await api.get("/campaigns")
  return response.data
}
```

### React компоненты

```tsx
// ✅ Хорошо: typed props, JSDoc
interface DashboardProps {
  /** ID кампании для фильтрации */
  campaignId?: string;
  /** Период для отображения (по умолчанию 30d) */
  range?: '7d' | '30d' | '90d';
}

export const Dashboard: React.FC<DashboardProps> = ({
  campaignId,
  range = '30d'
}) => {
  const { data, isLoading } = useCampaigns({ range });

  if (isLoading) return <Spinner />;

  return <div>...</div>;
};

// ❌ Плохо: без типов
export const Dashboard = ({ campaignId, range }) => {
  ...
};
```

### Стили и Цвета

#### Философия

Мы используем систему семантических токенов и перцептуальные цветовые шкалы (например, OKLCH) для обеспечения визуальной консистентности, доступности и лёгкости поддержки/редизайна. Вместо фиксированных цветов мы используем шкалы оттенков (50–900), где каждый оттенок имеет предсказуемую светлоту.

**Запрещено** использовать хардкод-значения цветов (например, `red`, `#FFF`) напрямую в стилях. Всегда обращайтесь к цветам из темы `tailwind.config.js`.

#### Рекомендованные шкалы

- **dc-primary (50-900):** Якорь бренда. Для ключевых действий, ссылок, акцентов, состояний hover/active.
- **dc-accent (50-900):** Вторичный акцент. Для иллюстративных элементов, второстепенных CTA.
- **dc-neutral (50-900):** Холодные серые. Для бордеров, иконок, разделителей, второстепенного текста.
- **dc-warm (50-400):** Тёплые бежевые. Для фоновых подложек и слоёв.
- **dc-success | warn | danger (100-700):** Семантические статусы для уведомлений и валидации. Сделаны "тише" (менее насыщены), чтобы не спорить с брендом.

#### Карта применений (шпаргалка)

- **Фоны:**
  - Основной фон страницы: `bg-dc-warm-100` или `bg-dc-neutral-50`.
  - Фон карточек/элементов: `bg-white` или `bg-dc-warm-200`.
  - Ховер-состояния для фонов: `hover:bg-dc-primary-50` или `hover:bg-dc-neutral-100`.

- **Текст:**
  - Основной: `text-dc-ink` (или `text-dc-neutral-900`).
  - Второстепенный: `text-dc-neutral-600`.
  - Неактивный (disabled): `text-dc-neutral-400`.

- **Бордеры и разделители:**
  - `border-dc-neutral-200` или `border-dc-neutral-300`.

- **Кнопки (Button):**
  - Основная: `bg-dc-primary-500` → `hover:bg-dc-primary-600` → `active:bg-dc-primary-700`.
  - С контуром (outline): `border-dc-primary-300 text-dc-primary-500`.

- **Статусы:**
  - Фон: `bg-dc-success-50`.
  - Текст/Иконка: `text-dc-success-700`.
  - (Аналогично для `warn` и `danger`).

#### Доступность (Accessibility)

Необходимо соблюдать минимальные коэффициенты контрастности:
- **AA (Минимум):** Текст к фону ≥ **4.5:1**. Крупный текст (≥18pt) ≥ **3:1**.
- Интерактивные элементы должны быть различимы без цвета (например, за счет изменения фона, рамки или иконки при фокусе/наведении).

## SQL

### Именование
- **Таблицы:** `snake_case` (plural: `campaigns`, `leads`)
- **Колонки:** `snake_case`
- **Индексы:** `idx_{table}_{columns}`
- **Foreign keys:** `fk_{table}_{ref_table}`

```sql
-- ✅ Хорошо
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    budget_rub NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campaigns_status ON campaigns(status);

-- ❌ Плохо (CamelCase, нет типов размеров)
CREATE TABLE Campaign (
    ID uuid PRIMARY KEY,
    Title VARCHAR,
    BudgetRub NUMERIC
);
```

### Форматирование
- **Ключевые слова:** UPPERCASE
- **Отступы:** 2 spaces
- **Один столбец на строку** в SELECT

```sql
-- ✅ Хорошо
SELECT
  c.id,
  c.title,
  SUM(s.spend_rub) AS total_spend,
  COUNT(l.id) AS leads_count
FROM campaigns c
LEFT JOIN spend_daily s ON c.id = s.campaign_id
LEFT JOIN leads l ON l.utm_campaign = c.title
WHERE c.status = 'active'
GROUP BY c.id, c.title
ORDER BY total_spend DESC;

-- ❌ Плохо
select c.id,c.title,sum(s.spend_rub) as total_spend from campaigns c left join spend_daily s on c.id=s.campaign_id where c.status='active';
```

## Git Commits

### Формат
```
<type>: <short description>

<optional longer description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types
- `feat:` — новая функция
- `fix:` — исправление бага
- `refactor:` — рефакторинг без изменения функциональности
- `test:` — добавление/изменение тестов
- `docs:` — обновление документации
- `chore:` — обслуживание (зависимости, CI и т.д.)

### Примеры
```bash
# ✅ Хорошо
git commit -m "feat: add AI Analyst weekly reports

Implements AnalystAgent with GPT-4 integration.
Generates weekly reports every Monday at 9:00.
Saves reports to analyst_reports table.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# ❌ Плохо
git commit -m "fixed stuff"
```

## Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.2
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

Установка:
```bash
pip install pre-commit
pre-commit install
```

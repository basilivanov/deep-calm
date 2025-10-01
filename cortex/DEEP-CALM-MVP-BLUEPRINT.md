# DeepCalm MVP — Blueprint для LLM

## Контекст проекта

**Продукт:** Автопилот performance-маркетинга для массажного кабинета
**Владелец:** Василий (solo-founder, арендует кабинет, окончил обучение)
**Задача:** Запустить рекламу на 3 площадках (VK, Директ, Avito), тестировать креативы A/B, контролировать unit-экономику (CAC ≤ 500₽, ROAS ≥ 5.0)

**LLM роль:** Пишет ВСЁ с нуля (backend API + frontend админка + коннекторы + креативы)

---

## Архитектура

### Nexus (API + Jobs)
- **API**: FastAPI endpoints для аналитики, публикации, управления кампаниями
- **Jobs**: dc-jobs (nightly витрины, оффлайн-конверсии, синхронизация статистики)
- **Интеграции**: VK Ads, Яндекс.Директ, Avito, YCLIENTS, Яндекс.Метрика

### Cortex (Knowledge Base)
- **Docs-as-code**: STANDARDS.yml, METRICS_DICTIONARY.md, API specs, Event schemas
- **Политики**: Brandbook (тон, стоп-слова модерации), исключения SKU (TANTRA-120, YONI-240)
- **Контракты**: OpenAPI, JSONSchema для событий

### Aegis (Observability)
- **Alerts**: ingest_lag > 60min → retry, api_5xx_rate > 2% → pause publishing
- **Auto-remediation**: DQ-аномалии → recompute marts
- **Metrics**: Prometheus (CAC, ROAS, TTP, API latency)

### Admin UI (React/Vite)
- **Dashboard**: Графики CAC/Conv%/Spend по площадкам
- **Campaign Manager**: Создание/пауза/редактирование кампаний
- **Creative A/B Tests**: Загрузка креативов, просмотр результатов A/B тестов
- **Inbox**: Диалоги из TG/WA/Avito Messenger (позже)

---

## Приоритет #1: Publishing Automation

### User Story
```
Как владелец кабинета
Я хочу создать кампанию в админке (название, бюджет, SKU, площадки)
И LLM сгенерирует креативы (3 варианта текста + изображения)
И опубликует на VK/Директ/Avito
Чтобы я видел статистику (клики, конверсии, CAC) в одном месте
```

### MVP Scope (Фаза 1)
1. **Создание кампании** (админка → БД → очередь на публикацию)
2. **Генерация креативов** (LLM → brandbook-compliance → S3/YA storage)
3. **Публикация** (API коннекторы → VK/Директ/Avito)
4. **Сбор статистики** (nightly job → mart_sources: CAC/ROAS по каналам)
5. **Дашборд** (график CAC/Conv% за 30 дней, drill-down по кампаниям)

---

## Схема БД (PostgreSQL 16)

### Таблица: `channels` (справочник площадок)
```sql
CREATE TABLE channels (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL, -- vk, direct, avito
  name VARCHAR(100) NOT NULL,
  api_endpoint TEXT,
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица: `campaigns` (кампании)
```sql
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  sku VARCHAR(50) NOT NULL, -- RELAX-60, DEEP-90, etc.
  budget_rub NUMERIC(10,2),
  target_cac_rub NUMERIC(10,2) DEFAULT 500,
  target_roas NUMERIC(5,2) DEFAULT 5.0,
  channels TEXT[], -- ['vk', 'direct', 'avito']
  status VARCHAR(20) DEFAULT 'draft', -- draft|active|paused|stopped
  ab_test_enabled BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица: `creatives` (креативы для A/B тестов)
```sql
CREATE TABLE creatives (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  variant VARCHAR(10), -- A, B, C
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  image_url TEXT,
  cta TEXT, -- "Записаться", "Узнать больше"
  generated_by VARCHAR(50) DEFAULT 'llm', -- llm|manual
  moderation_status VARCHAR(20) DEFAULT 'pending', -- pending|approved|rejected
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица: `placements` (размещения на площадках)
```sql
CREATE TABLE placements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  creative_id UUID REFERENCES creatives(id) ON DELETE SET NULL,
  channel_code VARCHAR(20) REFERENCES channels(code),
  external_campaign_id TEXT, -- ID от VK/Директ/Avito
  external_ad_id TEXT,
  status VARCHAR(20) DEFAULT 'pending', -- pending|published|active|paused|failed
  error_message TEXT,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица: `spend_daily` (ежедневные расходы)
```sql
CREATE TABLE spend_daily (
  id SERIAL PRIMARY KEY,
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  channel_code VARCHAR(20) REFERENCES channels(code),
  date DATE NOT NULL,
  spend_rub NUMERIC(10,2) DEFAULT 0,
  clicks INT DEFAULT 0,
  impressions INT DEFAULT 0,
  synced_at TIMESTAMPTZ,
  UNIQUE(campaign_id, channel_code, date)
);
```

### Таблица: `leads` (лиды с лендинга/форм)
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone VARCHAR(20) NOT NULL, -- +79991234567
  utm_source VARCHAR(50), -- vk, direct, avito
  utm_campaign VARCHAR(100),
  utm_content VARCHAR(100), -- creative_id
  web_id TEXT, -- клиентский ID (cookie/localStorage)
  yclients_id INT, -- ID из YCLIENTS после записи
  first_touch_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(phone)
);
```

### Таблица: `bookings` (записи из YCLIENTS)
```sql
CREATE TABLE bookings (
  id SERIAL PRIMARY KEY,
  yclients_id INT UNIQUE NOT NULL,
  lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
  sku VARCHAR(50),
  starts_at TIMESTAMPTZ NOT NULL,
  status VARCHAR(20), -- confirmed|cancelled|completed
  price_rub NUMERIC(10,2),
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица: `conversions` (конверсии = booking confirmed)
```sql
CREATE TABLE conversions (
  id SERIAL PRIMARY KEY,
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  booking_id INT REFERENCES bookings(id) ON DELETE CASCADE,
  campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
  channel_code VARCHAR(20),
  ttp_days INT, -- Time To Purchase (days)
  revenue_rub NUMERIC(10,2),
  converted_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица: `settings` (настраиваемые параметры системы)
```sql
CREATE TABLE settings (
  key VARCHAR(100) PRIMARY KEY,
  value TEXT NOT NULL,
  value_type VARCHAR(20) NOT NULL, -- 'int', 'float', 'string', 'bool'
  category VARCHAR(50) NOT NULL, -- 'financial', 'pricing', 'alerts', 'ai', 'operational'
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_by VARCHAR(50) DEFAULT 'admin'
);

-- Начальные значения (seed)
INSERT INTO settings (key, value, value_type, category, description) VALUES
-- Финансовые показатели
('target_monthly_revenue_rub', '100000', 'int', 'financial', 'Целевая месячная выручка (спидометр в админке)'),
('target_cac_rub', '500', 'int', 'financial', 'Целевой CAC (можно увеличить если не укладываемся)'),
('target_roas', '5.0', 'float', 'financial', 'Целевой ROAS (Return on Ad Spend): выручка / расходы'),
('max_daily_spend_per_channel_rub', '2000', 'int', 'financial', 'Максимальный расход на канал в день'),

-- Цены на услуги (SKU)
('sku_relax60_price_rub', '3500', 'int', 'pricing', 'Цена SKU RELAX-60'),
('sku_relax90_price_rub', '4800', 'int', 'pricing', 'Цена SKU RELAX-90'),
('sku_deep90_price_rub', '4200', 'int', 'pricing', 'Цена SKU DEEP-90'),
('sku_therapy60_price_rub', '4200', 'int', 'pricing', 'Цена SKU THERAPY-60'),

-- Операционные лимиты
('max_monthly_clients', '80', 'int', 'operational', 'Максимум клиентов в месяц (ограничение при переборе)'),
('workload_capacity_hours_per_month', '160', 'int', 'operational', 'Пропускная способность (часов/месяц)'),

-- Алерты и пороги
('alert_cac_threshold_rub', '700', 'int', 'alerts', 'Отправить алерт если CAC превысит порог'),
('alert_roas_threshold', '3.0', 'float', 'alerts', 'Алерт при ROAS < 3.0 (окупаемость низкая)'),
('pause_campaign_if_cac_exceeds_rub', '1000', 'int', 'alerts', 'Автопауза кампании при CAC выше'),

-- AI поведение
('chatbot_confidence_threshold', '0.70', 'float', 'ai', 'Порог уверенности чатбота (эскалация при < 70%)'),
('creative_generation_temp', '0.8', 'float', 'ai', 'Temperature для GPT-4 при генерации креативов'),
('analyst_report_schedule_cron', '0 9 * * MON', 'string', 'ai', 'Расписание отчётов AI Аналитика (каждый понедельник 9:00)');
```

### Таблица: `analyst_reports` (отчёты AI Аналитика)
```sql
CREATE TABLE analyst_reports (
  id SERIAL PRIMARY KEY,
  report_type VARCHAR(50) NOT NULL, -- 'weekly', 'monthly', 'ad_hoc'
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  summary TEXT, -- краткое резюме (2-3 предложения)
  problems JSONB, -- массив проблем: ["CAC на VK выше на 40%", "Конверсия Avito упала"]
  recommendations JSONB, -- массив рекомендаций: [{"action": "увеличить бюджет VK", "reason": "...", "expected_impact": "..."}]
  settings_changes JSONB, -- предлагаемые изменения настроек: [{"key": "target_cac_rub", "current": 500, "proposed": 600, "reason": "..."}]
  channel_analysis JSONB, -- детали по каналам: [{"channel": "vk", "status": "good", "comment": "..."}]
  generated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Витрина: `mart_campaigns_daily` (агрегированная статистика)
```sql
CREATE MATERIALIZED VIEW mart_campaigns_daily AS
SELECT
  c.id AS campaign_id,
  c.title AS campaign_title,
  s.channel_code,
  s.date,
  SUM(s.spend_rub) AS spend,
  SUM(s.clicks) AS clicks,
  SUM(s.impressions) AS impressions,
  COUNT(DISTINCT conv.id) AS conversions,
  COALESCE(SUM(s.spend_rub) / NULLIF(COUNT(DISTINCT l.id), 0), 0) AS cac,
  COALESCE(SUM(conv.revenue_rub) / NULLIF(SUM(s.spend_rub), 0), 0) AS roas,
  COALESCE(SUM(conv.revenue_rub), 0) AS revenue
FROM campaigns c
LEFT JOIN spend_daily s ON c.id = s.campaign_id
LEFT JOIN leads l ON l.utm_campaign = c.title AND l.utm_source = s.channel_code AND DATE(l.first_touch_at) = s.date
LEFT JOIN conversions conv ON conv.lead_id = l.id
GROUP BY c.id, c.title, s.channel_code, s.date;
```

---

## API Endpoints (FastAPI)

### `/api/v1/campaigns` — управление кампаниями
```python
# GET /api/v1/campaigns — список всех кампаний
# POST /api/v1/campaigns — создать кампанию
# GET /api/v1/campaigns/{id} — детали кампании
# PATCH /api/v1/campaigns/{id} — обновить (budget, status)
# DELETE /api/v1/campaigns/{id} — удалить
```

### `/api/v1/creatives` — управление креативами
```python
# GET /api/v1/creatives?campaign_id={id} — креативы кампании
# POST /api/v1/creatives — создать креатив (или сгенерировать через LLM)
# POST /api/v1/creatives/generate — LLM генерирует 3 варианта
# DELETE /api/v1/creatives/{id} — удалить
```

### `/api/v1/publishing` — публикация
```python
# POST /api/v1/publishing/publish — опубликовать кампанию (enqueue job)
# GET /api/v1/publishing/status/{campaign_id} — статус публикации
# POST /api/v1/publishing/pause/{campaign_id} — приостановить
```

### `/api/v1/analytics` — аналитика
```python
# GET /api/v1/analytics/dashboard?range=30d — summary (CAC, ROAS, Conv%)
# GET /api/v1/analytics/campaigns/{id}?range=30d — детали кампании
# GET /api/v1/analytics/ab_tests/{campaign_id} — результаты A/B тестов
```

### `/api/v1/integrations` — управление интеграциями
```python
# POST /api/v1/integrations/vk/auth — OAuth для VK
# POST /api/v1/integrations/direct/auth — OAuth для Директ
# GET /api/v1/integrations/yclients/sync — форсировать синхронизацию
```

### `/api/v1/settings` — управление настройками
```python
# GET /api/v1/settings — все настройки (сгруппированы по категориям)
# GET /api/v1/settings/{key} — получить одну настройку
# PUT /api/v1/settings/{key} — обновить настройку
# Example: PUT /api/v1/settings/target_monthly_revenue_rub {"value": "150000", "updated_by": "vasily"}
```

### `/api/v1/analyst` — AI Аналитик
```python
# GET /api/v1/analyst/reports — список всех отчётов
# GET /api/v1/analyst/reports/{id} — детали отчёта
# POST /api/v1/analyst/generate — принудительно сгенерировать отчёт
# POST /api/v1/analyst/query — интерактивный вопрос к аналитику
# Example: POST /api/v1/analyst/query {"question": "Какой канал самый эффективный в сентябре?"}
```

---

## Интеграции (API коннекторы)

### VK Ads (myTarget)
**Статус:** Официального VK Ads API для создания кампаний не найдено в открытом доступе. Есть интеграции через myTarget (старая платформа).

**Альтернативы:**
1. **myTarget API** (если доступен) — создание кампаний
2. **Веб-скрапинг** через Selenium/Playwright (не рекомендуется, нарушает ToS)
3. **Ручная загрузка** через UI (временное решение для MVP)

**Для MVP:** создаём mock-коннектор, который логирует запросы и возвращает фейковые `external_campaign_id`.

```python
# app/integrations/vk_ads.py
async def create_campaign(title: str, budget: float, creative: dict) -> dict:
    # TODO: реальный API-запрос к VK Ads
    logger.info(f"VK: Creating campaign '{title}' with budget {budget}")
    return {"external_campaign_id": f"vk_camp_{uuid.uuid4().hex[:8]}"}
```

### Яндекс.Директ API v5
**Статус:** Полная документация доступна на `yandex.ru/dev/direct`

**Основные методы:**
- `campaigns.add` — создание кампании
- `adgroups.add` — создание группы объявлений
- `ads.add` — добавление объявлений
- `campaigns.update` — изменение бюджета/статуса

**OAuth:** через `yandex.ru/dev/oauth`

**Для MVP:** используем httpx для REST-запросов.

```python
# app/integrations/yandex_direct.py
async def create_campaign(token: str, title: str, budget: float) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.direct.yandex.com/json/v5/campaigns",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "method": "add",
                "params": {
                    "Campaigns": [{
                        "Name": title,
                        "StartDate": date.today().isoformat(),
                        "TextCampaign": {"BiddingStrategy": {"Search": {"BiddingStrategyType": "HIGHEST_POSITION"}}}
                    }]
                }
            }
        )
        return resp.json()
```

### Avito Автозагрузка (XML API)
**Статус:** Доступ через тарифы "Расширенный"/"Максимальный", документация в Swagger 3.0

**Метод:**
1. Формируем XML-файл с объявлениями (до 50K объявлений)
2. Загружаем через POST `/api/v2/items/upload`
3. Получаем отчёт на email (до 2 часов обработки)

**Для MVP:** генерируем XML, загружаем через API.

```python
# app/integrations/avito.py
async def upload_ads(token: str, ads: List[dict]) -> dict:
    xml = generate_avito_xml(ads)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.avito.ru/v2/items/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("ads.xml", xml, "application/xml")}
        )
        return resp.json()
```

### YCLIENTS API v2.0
**Документация:** `yclients.docs.apiary.io`

**Методы:**
- `GET /records` — записи клиентов
- `GET /clients` — клиенты
- `Webhooks` — события (booking.created, payment.captured)

**Для MVP:** poll через GET /records каждый час (nightly job).

```python
# app/integrations/yclients.py
async def fetch_bookings(token: str, company_id: int, date_from: date) -> List[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.yclients.com/api/v1/records/{company_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.yclients.v2+json"},
            params={"start_date": date_from.isoformat()}
        )
        return resp.json()["data"]
```

### Яндекс.Метрика API (оффлайн-конверсии)
**Документация:** `yandex.ru/dev/metrika/ru/management/openapi/offline_conversions`

**Метод:**
- `POST /management/v1/counter/{counterId}/offline_conversions/upload` — загрузка CSV

**Для MVP:** отправляем конверсии батчами (nightly job).

```python
# app/integrations/yandex_metrika.py
async def upload_conversions(token: str, counter_id: int, conversions: List[dict]):
    csv_data = generate_csv(conversions)  # ClientId, Target, DateTime, Price, Currency
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api-metrika.yandex.net/management/v1/counter/{counter_id}/offline_conversions/upload",
            headers={"Authorization": f"OAuth {token}"},
            files={"file": ("conversions.csv", csv_data, "text/csv")}
        )
        return resp.json()
```

---

## Nightly Jobs (dc-jobs)

### Job 1: `sync_spend` — синхронизация расходов
**Частота:** 1 раз в сутки (03:00)
**Источники:** VK Ads API, Директ API, Avito (нет API статистики — ручной экспорт CSV)
**Задача:** обновить `spend_daily` (расходы, клики, показы за вчера)

### Job 2: `sync_bookings` — синхронизация записей YCLIENTS
**Частота:** 1 раз в час
**Задача:** fetch новых bookings → сопоставить с `leads` по телефону → создать `conversions`

### Job 3: `compute_marts` — пересчёт витрин
**Частота:** 1 раз в сутки (04:00)
**Задача:** `REFRESH MATERIALIZED VIEW mart_campaigns_daily`

### Job 4: `upload_offline_conversions` — оффлайн-конверсии в Метрику
**Частота:** 1 раз в сутки (05:00)
**Задача:** отправить вчерашние конверсии в Метрику (ClientId = web_id, Target = "booking", Price = revenue)

### Job 5: `analyst_weekly_report` — еженедельный отчёт AI Аналитика
**Частота:** Каждый понедельник в 9:00 (настраивается в settings: analyst_report_schedule_cron)
**Задача:**
1. Загрузить данные за последние 7 дней (spend, leads, conversions по каналам)
2. Сравнить с целевыми показателями из `settings`
3. Сгенерировать отчёт через GPT-4: анализ, проблемы, рекомендации
4. Сохранить в `analyst_reports`
5. Отправить в Telegram владельцу

**Пример кода:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.analyst.agent import AnalystAgent

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', day_of_week='mon', hour=9, minute=0)
async def weekly_analyst_report():
    """Запускается каждый понедельник в 9:00"""
    logger.info("Starting weekly analyst report generation")

    agent = AnalystAgent()
    report = await agent.generate_weekly_report()

    logger.info(f"Report generated: {report['summary']}")

    # Отправить в Telegram
    await send_telegram_message(
        chat_id=settings.TG_CHAT_ID,
        text=f"📊 Еженедельный отчёт AI Аналитика:\n\n{report['summary']}\n\nПодробности в админке."
    )
```

---

## Admin UI (React + Vite)

### Компоненты

#### 1. `Dashboard.tsx` — главный экран
- **График CAC** (линия, 30 дней, по каналам)
- **График Conv%** (линия, 30 дней)
- **Сводка:** Spend за 30д, Leads, Conversions, CAC avg, ROAS avg
- **Таблица топ-кампаний** (по Conv%, drill-down)

#### 2. `CampaignsList.tsx` — список кампаний
- **Фильтры:** Status (active/paused), Channel (all/vk/direct/avito)
- **Действия:** Edit, Pause, Delete, View Analytics

#### 3. `CampaignForm.tsx` — создание кампании
- **Поля:** Title, SKU (select), Budget, Target CAC, Channels (multi-select)
- **Кнопка:** "Generate Creatives" → вызов `/api/v1/creatives/generate`

#### 4. `CreativesList.tsx` — креативы A/B
- **Карточки:** вариант A/B/C (title, body, image preview)
- **Метрики:** Clicks, Conv%, CAC (по варианту)
- **Действия:** Edit, Delete, Publish

#### 5. `IntegrationsPage.tsx` — управление токенами
- **VK Ads:** OAuth кнопка, статус подключения
- **Директ:** OAuth кнопка
- **Avito:** ручной ввод токена
- **YCLIENTS:** ручной ввод токена + Company ID
- **Метрика:** ручной ввод токена + Counter ID

#### 6. `SettingsPage.tsx` — настройки системы
- **Табы по категориям:** Финансы, Цены, Алерты, AI, Операционные
- **Circular Progress Bar:** Целевая выручка/месяц (спидометр)
- **Editable Fields:** каждая настройка с inline-редактированием
- **Сохранение:** PUT /api/v1/settings/{key} при изменении

**Пример UI:**
```tsx
<Tabs defaultValue="financial">
  <TabsList>
    <TabsTrigger value="financial">💰 Финансы</TabsTrigger>
    <TabsTrigger value="pricing">🏷️ Цены</TabsTrigger>
    <TabsTrigger value="alerts">🔔 Алерты</TabsTrigger>
    <TabsTrigger value="ai">🤖 AI</TabsTrigger>
  </TabsList>

  <TabsContent value="financial">
    {/* Спидометр для выручки */}
    <CircularProgressBar
      current={currentMonthRevenue}
      target={settings.target_monthly_revenue_rub}
      label="Выручка за месяц"
    />

    {/* Редактируемые поля */}
    <SettingField
      keyName="target_monthly_revenue_rub"
      label="Целевая выручка/месяц"
      type="number"
      suffix="₽"
      onSave={(value) => updateSetting('target_monthly_revenue_rub', value)}
    />

    <SettingField
      keyName="target_cac_rub"
      label="Целевой CAC"
      type="number"
      suffix="₽"
    />
  </TabsContent>
</Tabs>
```

#### 7. `AnalystPage.tsx` — AI Аналитик
- **Последний отчёт:** Краткое резюме, проблемы, рекомендации с кнопками "Применить"
- **Интерактивный чат:** Текстовое поле для вопросов к аналитику
- **История отчётов:** Таблица прошлых отчётов (weekly/monthly)

**Пример UI:**
```tsx
<div className="analyst-page">
  {/* 1. Последний еженедельный отчёт */}
  <Card>
    <CardHeader>
      <h2>📊 Отчёт за неделю (23-29 сентября)</h2>
    </CardHeader>
    <CardContent>
      <div className="summary">{report.summary}</div>

      <h3>Проблемы:</h3>
      <ul>
        {report.problems.map(p => <li>⚠️ {p}</li>)}
      </ul>

      <h3>Рекомендации:</h3>
      {report.recommendations.map(rec => (
        <RecommendationCard
          action={rec.action}
          reason={rec.reason}
          expectedImpact={rec.expected_impact}
          onApply={() => applyRecommendation(rec)}
        />
      ))}

      {/* Предлагаемые изменения настроек */}
      {report.settings_changes.length > 0 && (
        <>
          <h3>Предлагаемые изменения настроек:</h3>
          {report.settings_changes.map(change => (
            <SettingChangeCard
              setting={change.key}
              current={change.current}
              proposed={change.proposed}
              reason={change.reason}
              onApply={() => applySetting(change.key, change.proposed)}
            />
          ))}
        </>
      )}
    </CardContent>
  </Card>

  {/* 2. Интерактивный чат */}
  <Card>
    <CardHeader>
      <h2>💬 Задать вопрос аналитику</h2>
    </CardHeader>
    <CardContent>
      <ChatInterface
        onSubmit={async (question) => {
          const answer = await api.post('/analyst/query', { question });
          return answer;
        }}
        placeholder="Например: Какой канал приносит больше всего конверсий в сентябре?"
      />
    </CardContent>
  </Card>

  {/* 3. История отчётов */}
  <Card>
    <CardHeader>
      <h2>📚 Архив отчётов</h2>
    </CardHeader>
    <CardContent>
      <ReportsList reports={pastReports} />
    </CardContent>
  </Card>
</div>
```

---

## Cortex Documentation (для LLM)

### `cortex/INTEGRATIONS.md`
```markdown
# Integrations Guide

## VK Ads
- **Status:** MVP uses mock connector (no official API for campaign creation found)
- **TODO:** Explore myTarget API or manual upload
- **Auth:** OAuth 2.0 (когда доступ появится)

## Яндекс.Директ
- **API:** https://yandex.ru/dev/direct/doc/ru/concepts/overview
- **Methods:** campaigns.add, adgroups.add, ads.add
- **Auth:** OAuth 2.0 (токен через yandex.ru/dev/oauth)
- **Limits:** 10K запросов/день

## Avito
- **API:** XML автозагрузка (Swagger 3.0)
- **Requirements:** Тариф "Расширенный"/"Максимальный"
- **Limits:** 50K объявлений/файл, 1GB max, обработка до 2 часов

## YCLIENTS
- **API:** https://yclients.docs.apiary.io
- **Methods:** GET /records, GET /clients
- **Webhooks:** deprecated (используем polling)
- **Auth:** User token (yclients.com/settings/api)

## Яндекс.Метрика
- **API:** https://yandex.ru/dev/metrika/ru/management/openapi/offline_conversions
- **Method:** POST /offline_conversions/upload (CSV)
- **Format:** ClientId, Target, DateTime, Price, Currency
```

### `cortex/brandbook/creative_rules.md`
```markdown
# Creative Generation Rules

## Tone of Voice
- Мягко, без агрессии
- "Тишина на час", "Без боли", "Глубокое расслабление"
- Избегать медицинских терминов

## Moderation Stop-Words (для Avito/VK)
- ❌ "эротический", "интимный", "тантра" (риск блокировки)
- ✅ "расслабляющий", "глубокий", "авторский массаж"

## CTA Examples
- "Записаться на сеанс"
- "Узнать свободное время"
- "Забронировать час тишины"

## Image Guidelines
- Нейтральные тона (бежевый, белый)
- Без явных изображений тела
- Акцент на атмосферу (свечи, ткани, руки массажиста)

## SKU Exclusions (не рекламируем)
- TANTRA-120, YONI-240 (высокий риск модерации)
```

---

## Seed Data (фейковые данные для тестов)

### `tests/fixtures/campaigns.json`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Запуск сентябрь — Релакс",
    "sku": "RELAX-60",
    "budget_rub": 15000,
    "target_cac_rub": 450,
    "channels": ["vk", "direct"],
    "status": "active",
    "ab_test_enabled": true
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "title": "Avito — Глубокий массаж",
    "sku": "DEEP-90",
    "budget_rub": 10000,
    "channels": ["avito"],
    "status": "active"
  }
]
```

### `tests/fixtures/spend_daily.json` (30 дней данных)
```json
[
  {"campaign_id": "550e8400-e29b-41d4-a716-446655440001", "channel_code": "vk", "date": "2025-09-01", "spend_rub": 450, "clicks": 25, "impressions": 1200},
  {"campaign_id": "550e8400-e29b-41d4-a716-446655440001", "channel_code": "vk", "date": "2025-09-02", "spend_rub": 520, "clicks": 30, "impressions": 1350}
]
```

### `tests/fixtures/conversions.json`
```json
[
  {"lead_id": "...", "campaign_id": "550e8400-e29b-41d4-a716-446655440001", "channel_code": "vk", "ttp_days": 2, "revenue_rub": 3500, "converted_at": "2025-09-03T14:00:00Z"}
]
```

---

## TASKS/0001 для LLM

**Title:** Реализовать Publishing API + Campaign Dashboard

**Acceptance Criteria:**
1. ✅ Создание кампании через POST /api/v1/campaigns
2. ✅ Генерация 3 креативов (A/B/C) через POST /api/v1/creatives/generate (mock LLM)
3. ✅ Публикация на VK/Директ/Avito (mock коннекторы)
4. ✅ Dashboard показывает CAC/Conv% за 30д (график + таблица)
5. ✅ Все тесты проходят (pytest coverage ≥70%)

**Files to Create:**
- `app/api/v1/campaigns.py` — CRUD endpoints
- `app/api/v1/creatives.py` — генерация креативов
- `app/api/v1/publishing.py` — публикация
- `app/api/v1/analytics.py` — dashboard data
- `app/integrations/vk_ads.py` — mock
- `app/integrations/yandex_direct.py` — реальный API
- `app/integrations/avito.py` — XML upload
- `tests/test_campaigns.py` — тесты
- `app/ui/src/pages/Dashboard.tsx` — React компонент

**Context Pack:** `dc-context 0001` → STANDARDS, METRICS_DICTIONARY, INTEGRATIONS.md, brandbook/creative_rules.md

---

## AI Аналитик (Phase 1.5)

**Когда запускать:** После 7 дней работы кампаний (чтобы было достаточно данных для анализа)

### Архитектура AnalystAgent

```python
# app/analyst/agent.py
import openai
from datetime import date, timedelta
from app.db import get_session
from app.models import Campaign, SpendDaily, Lead, Conversion, Setting

class AnalystAgent:
    """
    AI-агент для анализа данных и рекомендаций.
    Использует GPT-4 + SQL-запросы к БД.
    """

    async def generate_weekly_report(self) -> dict:
        """
        Еженедельный отчёт (по понедельникам в 9:00)
        """
        # 1. Загрузить данные за последние 7 дней
        stats = await self._fetch_weekly_stats()

        # 2. Сравнить с целевыми показателями из settings
        settings = await self._get_settings()

        # 3. Подготовить prompt для GPT-4
        prompt = f"""
Ты — аналитик рекламных кампаний для массажного кабинета.

Данные за последние 7 дней:
- Потрачено: {stats['total_spend']}₽
- Лидов: {stats['leads_count']}
- Конверсий: {stats['conversions_count']}
- Выручка: {stats['revenue']}₽
- CAC: {stats['cac']}₽
- ROAS: {stats['roas']}

Целевые показатели (из настроек):
- Целевой CAC: {settings['target_cac_rub']}₽
- Целевой ROAS: {settings['target_roas']}
- Цель выручки/месяц: {settings['target_monthly_revenue_rub']}₽

Каналы (детально):
{json.dumps(stats['by_channel'], indent=2, ensure_ascii=False)}

Задача:
1. Проанализируй эффективность каждого канала
2. Найди проблемы (если CAC высокий, конверсия низкая и т.д.)
3. Дай 3-5 конкретных рекомендаций
4. Предложи изменения в бюджетах/настройках

Формат ответа: JSON
{{
  "summary": "краткое резюме 2-3 предложения",
  "channel_analysis": [{{"channel": "vk", "status": "good/bad", "comment": "..."}}],
  "problems": ["проблема 1", "проблема 2"],
  "recommendations": [
    {{"action": "увеличить бюджет VK на 30%", "reason": "...", "expected_impact": "..."}}
  ],
  "settings_changes": [
    {{"key": "target_cac_rub", "current": 500, "proposed": 600, "reason": "..."}}
  ]
}}
"""

        # 4. Вызвать GPT-4
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        report = json.loads(response.choices[0].message.content)

        # 5. Сохранить отчёт в БД
        await self._save_report(report)

        # 6. Отправить в Telegram
        await self._send_to_telegram(report)

        return report

    async def chat_query(self, user_question: str) -> str:
        """
        Интерактивный чат для произвольных вопросов.
        Пример: "Какой канал самый эффективный в сентябре?"
        """
        # 1. Определить какие данные нужны (GPT-4 генерирует SQL)
        sql_prompt = f"""
Дана схема БД:
- campaigns (id, title, sku, budget_rub, status)
- spend_daily (campaign_id, channel, date, spend_rub, impressions, clicks, ctr)
- leads (id, phone, utm_source, utm_campaign, first_touch_at)
- conversions (id, lead_id, revenue_rub, ttp_days, converted_at)

Вопрос пользователя: "{user_question}"

Сгенерируй SQL-запрос для получения нужных данных.
"""

        sql_query = await self._generate_sql(sql_prompt)

        # 2. Выполнить запрос
        data = await self._execute_query(sql_query)

        # 3. Проанализировать результат и дать ответ
        answer_prompt = f"""
Вопрос: {user_question}
Данные из БД: {json.dumps(data, ensure_ascii=False)}

Дай понятный ответ на русском языке (2-4 предложения).
"""

        answer = await self._call_gpt(answer_prompt)
        return answer

    async def _fetch_weekly_stats(self) -> dict:
        """Загрузить статистику за 7 дней"""
        date_from = date.today() - timedelta(days=7)
        session = get_session()

        # Aggregate stats
        total_spend = session.query(func.sum(SpendDaily.spend_rub)).filter(
            SpendDaily.date >= date_from
        ).scalar() or 0

        leads_count = session.query(func.count(Lead.id)).filter(
            Lead.first_touch_at >= date_from
        ).scalar() or 0

        conversions_count = session.query(func.count(Conversion.id)).filter(
            Conversion.converted_at >= date_from
        ).scalar() or 0

        revenue = session.query(func.sum(Conversion.revenue_rub)).filter(
            Conversion.converted_at >= date_from
        ).scalar() or 0

        cac = total_spend / leads_count if leads_count > 0 else 0
        roas = revenue / total_spend if total_spend > 0 else 0

        # By channel
        by_channel = session.query(
            SpendDaily.channel_code,
            func.sum(SpendDaily.spend_rub).label('spend'),
            func.count(Lead.id).label('leads')
        ).outerjoin(Lead, Lead.utm_source == SpendDaily.channel_code).filter(
            SpendDaily.date >= date_from
        ).group_by(SpendDaily.channel_code).all()

        return {
            'total_spend': float(total_spend),
            'leads_count': leads_count,
            'conversions_count': conversions_count,
            'revenue': float(revenue),
            'cac': round(cac, 2),
            'roas': round(roas, 2),
            'by_channel': [{'channel': ch, 'spend': float(sp), 'leads': ld} for ch, sp, ld in by_channel]
        }

    async def _get_settings(self) -> dict:
        """Загрузить настройки из БД"""
        session = get_session()
        settings = session.query(Setting).all()
        return {s.key: s.value for s in settings}
```

### Использование настроек в коде

**Пример:** Автопауза кампании при превышении CAC

```python
# app/jobs/check_cac_alerts.py
async def check_cac_thresholds():
    """Проверка CAC и автопауза при превышении"""
    settings = await get_settings()
    pause_threshold = int(settings['pause_campaign_if_cac_exceeds_rub'])

    # Получить кампании с CAC > threshold
    campaigns = session.query(Campaign).filter(Campaign.status == 'active').all()

    for campaign in campaigns:
        cac = calculate_campaign_cac(campaign.id)

        if cac > pause_threshold:
            logger.warning(f"Campaign {campaign.title}: CAC {cac}₽ > {pause_threshold}₽, pausing")
            campaign.status = 'paused'
            session.commit()

            # Отправить алерт
            await send_telegram_alert(
                f"⚠️ Кампания '{campaign.title}' приостановлена: CAC {cac}₽ > {pause_threshold}₽"
            )
```

**Пример:** Использование настроек в UI (спидометр выручки)

```tsx
// components/RevenueSpeedometer.tsx
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';

function RevenueSpeedometer() {
  const { data: settings } = useSettings();
  const { data: currentRevenue } = useCurrentMonthRevenue();

  const target = parseInt(settings.target_monthly_revenue_rub);
  const current = currentRevenue || 0;
  const percentage = (current / target) * 100;

  return (
    <div className="speedometer">
      <CircularProgressbar
        value={percentage}
        text={`${Math.round(percentage)}%`}
        styles={buildStyles({
          pathColor: percentage >= 100 ? '#10b981' : '#3b82f6',
          textColor: '#1f2937',
          trailColor: '#e5e7eb',
        })}
      />
      <div className="speedometer-labels">
        <span>Текущая: {current.toLocaleString('ru-RU')}₽</span>
        <span>Цель: {target.toLocaleString('ru-RU')}₽</span>
      </div>
    </div>
  );
}
```

---

## Следующие шаги

1. **Запустить bootstrap:** `sudo bash deep-calm-bootstrap.sh`
2. **LLM essentials:** `sudo bash deep-calm-llm-essentials.sh` (Python, FastAPI, DB schema)
3. **Cortex docs:** `sudo bash deep-calm-cortex-additions.sh`
4. **Задача LLM:** `dc-context 0001` → начать разработку
5. **Токены интеграций:** добавить в `.env` (VK, Директ, Avito, YCLIENTS, Метрика)
6. **Тестирование:** seed data → проверка Dashboard
7. **Production:** `deep-calm-production-ready.sh` (CI/CD, metrics, Alembic)

---

**Этот документ — единственный источник правды для LLM. Всё остальное — детали реализации.**
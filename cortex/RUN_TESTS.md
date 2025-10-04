# RUN_TESTS

## Backend (pytest)
- Убедись, что dev-стек поднят: `cd /opt/deep-calm/dev && docker compose up -d`
- Запуск всех тестов из контейнера: `docker compose exec dc-api pytest -v`
- С покрытием: `docker compose exec dc-api pytest --cov=app --cov-report=term-missing`
- Нужно обратиться к другой БД? Переопредели `TEST_DATABASE_URL` перед запуском: `TEST_DATABASE_URL=postgresql://dc:dcpass@localhost:5432/deep_calm_test docker compose exec dc-api pytest …`

## Frontend (Vitest)
- Перейти в `frontend/`: `cd /opt/deep-calm/frontend`
- Одноразовый прогон: `npm run test`
- Watch-режим: `npm run test -- --watch`

**Что проверяем:**
- `AIChat.test.tsx` — диалог с ассистентом, ответы на POST `/api/v1/analyst/chat`
- `MetricCard.test.tsx` — отрисовка KPI блоков
- `Dashboard.test.tsx` — загрузка сводки метрик из `analyticsApi.dashboard`
- `AIAnalyst.test.tsx` — список кампаний, статус AI сервиса, fallback при ошибках API

# DeepCalm — AGENT READ ME (Entry)
Фокус: CAC≤500, ДРР≤20%, TTP контролируем. Ритуал: **TDD (красный→зелёный→рефакторинг)**, стандарты обязательны, CLI `dc`.

## Порядок
1) Прочитай `STANDARDS.yml`, `brandbook/invariants_v1.md`.
2) Обнови контракты: `APIs/openapi.yaml`, `EVENTS/*.schema.json`.
3) Напиши тесты (acceptance/unit/contract/DQ), запусти локально.
4) Минимальный код → зелёный → рефакторинг.
5) Обнови доки (`README.md`, ADR, политики) → PR (CI гейты обязательны).

## Команды
- `dc --env dev up|down|ps|logs|build|pull|restart|deploy|health|backup`
- `dc nginx:test|nginx:reload|nginx:logs`
- DEV-порты: API `127.0.0.1:8082 → 8000`, фронт `127.0.0.1:8083 → 3000`

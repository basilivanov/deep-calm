# TESTPLAN
Пирамида: acceptance → unit → contract → DQ → E2E (smoke). TDD обязательно.
- Acceptance: Lead→Booking→Payment→TTP (края: 0/1 день, пропуски UTM)
- Unit: CAC/DRR/TTP/Payback (границы/округления)
- Contract: OpenAPI (schemathesis), EVENTS (jsonschema)
- DQ-nightly: даты из будущего, дубликаты, пустые UTM, лаг ingest
- E2E: Playwright-smoke (Dashboard → Cohorts/TTP → mock create booking)

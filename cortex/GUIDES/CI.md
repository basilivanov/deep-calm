# CI Guide
- Test-first: PR без падающего теста блокируется (policy-guard).
- Гейты: unit/integration, schemathesis, DQ-smoke, e2e-smoke, coverage.
- Changed-files rule: изменения в api/analytics требуют tests/.

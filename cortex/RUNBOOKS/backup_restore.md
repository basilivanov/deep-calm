# Runbook: Backup/Restore
Тест бэкапа: `dc backup` → проверь Я.Диск `/Apps/deep-calm/backups/`.
Восстановление: `pg_restore -h 127.0.0.1 -p 5432 -U dc -d dc_dev < dump`.

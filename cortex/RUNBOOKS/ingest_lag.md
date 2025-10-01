# Runbook: Ingest lag > 60m
Действия: `dc --env dev logs`, перезапуск коннектора, проверка токенов.
Авто: Aegis → retry_sync(yclients). Эскалация: sev-2 (TG).

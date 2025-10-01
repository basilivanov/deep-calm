# NGINX Configuration Guide

## Overview

NGINX используется как reverse proxy для маршрутизации запросов между frontend и backend.

---

## Configurations

### DEV Environment (`infra/nginx/dev.conf`)

**Domain:** dev.dc.vasiliy-ivanov.ru
**Listen:** 80

**Routing:**
- `/api/healthz` → `http://127.0.0.1:8000/health` (Backend healthcheck)
- `/api/*` → `http://127.0.0.1:8000/` (Backend API, слэш убирает /api prefix)
- `/` → `http://127.0.0.1:3000` (Frontend admin)

**Backend:** dc-dev-api (127.0.0.1:8000)
**Frontend:** dc-dev-admin (127.0.0.1:3000)

### TEST Environment (`infra/nginx/test.conf`)

**Domain:** test.dc.vasiliy-ivanov.ru
**Listen:** 80

**Routing:**
- `/api/*` → `http://127.0.0.1:8001/` (Backend API test)
- `/` → `http://127.0.0.1:3001` (Frontend test)

**Backend:** dc-test-api (127.0.0.1:8001)
**Frontend:** dc-test-admin (127.0.0.1:3001)

---

## Port Allocation (Simple Schema)

| Environment | Frontend | Backend API | PostgreSQL | Redis |
|-------------|----------|-------------|------------|-------|
| **dev**     | 3000     | 8000        | internal   | internal |
| **test**    | 3001     | 8001        | internal   | internal |
| **staging** | 3002     | 8002        | internal   | internal |
| **prod**    | internal | internal    | internal   | internal |

**Логика:** Простые стандартные порты с инкрементом для каждого окружения

---

## Installation

```bash
# Установка конфига (DEV)
sudo cp /opt/deep-calm/infra/nginx/dev.conf /etc/nginx/sites-available/dev.dc
sudo ln -s /etc/nginx/sites-available/dev.dc /etc/nginx/sites-enabled/

# Установка конфига (TEST)
sudo cp /opt/deep-calm/infra/nginx/test.conf /etc/nginx/sites-available/test.dc
sudo ln -s /etc/nginx/sites-available/test.dc /etc/nginx/sites-enabled/

# Проверка конфига
sudo nginx -t

# Применить изменения
sudo systemctl reload nginx

# Или перезапуск
sudo systemctl restart nginx
```

---

## SSL/TLS (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx

# Получить сертификат для DEV
sudo certbot --nginx -d dev.dc.vasiliy-ivanov.ru

# Получить сертификат для TEST
sudo certbot --nginx -d test.dc.vasiliy-ivanov.ru

# Автообновление (уже настроено)
sudo systemctl status certbot.timer
```

После получения сертификата:
- Включить HSTS
- Редирект HTTP → HTTPS (certbot делает автоматически)

---

## Security Headers

Добавить в server блок после получения SSL:

```nginx
# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

## Rate Limiting (TODO Phase 2)

```nginx
# В http блок /etc/nginx/nginx.conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=publishing_limit:10m rate=1r/s;

# В location блоки
location /api/v1/publishing/ {
    limit_req zone=publishing_limit burst=5;
    proxy_pass http://127.0.0.1:8082/;
}
```

---

## Monitoring

```bash
# Проверка статуса
sudo systemctl status nginx

# Логи access
sudo tail -f /var/log/nginx/access.log

# Логи error
sudo tail -f /var/log/nginx/error.log

# Проверка конфига
sudo nginx -t

# Reload без даунтайма
sudo nginx -s reload
```

---

## Troubleshooting

### 502 Bad Gateway
- Проверить, что backend запущен: `docker ps | grep dc-dev-api`
- Проверить порт: `curl http://127.0.0.1:8000/health`
- Проверить логи nginx: `sudo tail -f /var/log/nginx/error.log`

### 504 Gateway Timeout
- Увеличить `proxy_read_timeout` в конфиге (сейчас 60s)

### Connection refused
- Проверить firewall: `sudo ufw status`
- Проверить, что контейнеры слушают на 127.0.0.1:
  - `netstat -tlnp | grep 3000` (frontend)
  - `netstat -tlnp | grep 8000` (API)

---

## TODO

- [x] Исправлено: простая схема портов (3000/8000, 3001/8001, etc)
- [ ] Добавить rate limiting для /api/v1/publishing
- [ ] Настроить логирование в JSON формат
- [ ] Добавить nginx status endpoint (/nginx_status)
- [ ] Настроить log rotation

# NGINX Guide
- TLS: Let’s Encrypt через certbot nginx.
- HSTS: включить после получения TLS.
- Rate-limit: на /bots и /publishing (позже).
- Health: /healthz проксируется в dc-api.
Операции: `dc nginx:test`, `dc nginx:reload`, логи: `dc nginx:logs`.

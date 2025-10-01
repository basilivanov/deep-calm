# Multi-stage build для оптимизации размера образа

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder /root/.local /root/.local

# Устанавливаем runtime зависимости
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Добавляем Python packages в PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Копируем код приложения
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

# Создаём непривилегированного пользователя
RUN useradd -m -u 1000 dcuser && chown -R dcuser:dcuser /app
USER dcuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose порт
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
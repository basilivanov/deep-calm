"""
DeepCalm — FastAPI Application

Main application entry point.
Следует DEEP-CALM-MVP-BLUEPRINT.md и STANDARDS.yml
"""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.logging import setup_logging


# Настройка логирования
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle события приложения (startup/shutdown).

    Startup:
    - Логирование старта приложения
    - Экспорт OpenAPI схемы в cortex/APIs/

    Shutdown:
    - Логирование остановки
    """
    # Startup
    logger.info(
        "application_startup",
        env=settings.app_env,
        debug=settings.app_debug,
        app="deep-calm",
        svc="dc-api"
    )

    yield

    # Shutdown
    logger.info("application_shutdown")


# FastAPI app
app = FastAPI(
    title="DeepCalm API",
    version="0.1.0",
    description="Performance-маркетинг автопилот для массажного кабинета",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """
    Добавляет correlation_id в контекст каждого запроса.

    Correlation ID используется для трейсинга запросов через все слои системы.
    Если клиент передаёт X-Correlation-ID, используем его, иначе генерируем новый.

    Args:
        request: FastAPI Request
        call_next: Следующий middleware

    Returns:
        Response с заголовком X-Correlation-ID
    """
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

    # Добавляем в structlog context
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        route=request.url.path,
        method=request.method
    )

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик исключений.

    Логирует все необработанные исключения и возвращает 500.

    Args:
        request: FastAPI Request
        exc: Exception

    Returns:
        JSONResponse с ошибкой
    """
    logger.error(
        "unhandled_exception",
        error=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Статус сервиса и версия

    Examples:
        >>> curl http://localhost:8000/health
        >>> {"status": "ok", "service": "dc-api", "version": "0.1.0"}
    """
    return {
        "status": "ok",
        "service": "dc-api",
        "version": "0.1.0",
        "env": settings.app_env
    }


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Приветственное сообщение
    """
    return {
        "message": "DeepCalm API",
        "docs": "/docs",
        "health": "/health"
    }


# TODO: Подключить роутеры API v1
# from app.api.v1 import campaigns, creatives, publishing, analytics
# app.include_router(campaigns.router, prefix="/api/v1", tags=["campaigns"])
# app.include_router(creatives.router, prefix="/api/v1", tags=["creatives"])
# app.include_router(publishing.router, prefix="/api/v1", tags=["publishing"])
# app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])

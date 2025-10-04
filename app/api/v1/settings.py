"""
DeepCalm — Settings API

CRUD endpoints для управления настройками системы.
Поддерживает конфигурацию AI Analyst и других компонентов.
"""
from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.core.db import get_db
from app.models.setting import Setting
from app.schemas.setting import (
    SettingCreate,
    SettingUpdate,
    SettingResponse,
    SettingListResponse,
    SettingValueResponse,
    BulkSettingsUpdate,
    SettingsByCategory
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def _convert_value(value: str, value_type: str) -> Union[str, int, float, bool]:
    """Конвертирует строковое значение в нужный тип"""
    try:
        if value_type == 'int':
            return int(value)
        elif value_type == 'float':
            return float(value)
        elif value_type == 'bool':
            return value.lower() in ('true', '1', 'yes', 'on')
        else:  # string
            return value
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail=f"Невозможно преобразовать '{value}' в тип {value_type}"
        )


@router.get("/settings", response_model=SettingListResponse)
def get_settings(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по ключу или описанию"),
    db: Session = Depends(get_db)
):
    """
    Получить список настроек с пагинацией и фильтрацией
    """
    logger.info("get_settings", page=page, page_size=page_size, category=category, search=search)

    query = db.query(Setting)

    # Фильтр по категории
    if category:
        query = query.filter(Setting.category == category)

    # Поиск по ключу или описанию
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            Setting.key.ilike(search_pattern) |
            Setting.description.ilike(search_pattern)
        )

    # Подсчет общего количества
    total = query.count()

    # Пагинация
    offset = (page - 1) * page_size
    settings = query.order_by(Setting.category, Setting.key).offset(offset).limit(page_size).all()

    pages = (total + page_size - 1) // page_size

    return SettingListResponse(
        settings=settings,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/settings/categories", response_model=List[SettingsByCategory])
def get_settings_by_categories(db: Session = Depends(get_db)):
    """
    Получить настройки, сгруппированные по категориям
    """
    logger.info("get_settings_by_categories")

    # Получаем все категории
    categories = db.query(Setting.category).distinct().all()
    result = []

    for (category,) in categories:
        settings = db.query(Setting).filter(Setting.category == category).order_by(Setting.key).all()
        result.append(SettingsByCategory(
            category=category,
            settings=settings,
            count=len(settings)
        ))

    return result


@router.get("/settings/{key}", response_model=SettingResponse)
def get_setting(key: str, db: Session = Depends(get_db)):
    """
    Получить настройку по ключу
    """
    logger.info("get_setting", key=key)

    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Настройка '{key}' не найдена")

    return setting


@router.get("/settings/{key}/value", response_model=SettingValueResponse)
def get_setting_value(key: str, db: Session = Depends(get_db)):
    """
    Получить типизированное значение настройки
    """
    logger.info("get_setting_value", key=key)

    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Настройка '{key}' не найдена")

    typed_value = _convert_value(setting.value, setting.value_type)

    return SettingValueResponse(
        key=setting.key,
        value=typed_value,
        value_type=setting.value_type,
        category=setting.category
    )


@router.post("/settings", response_model=SettingResponse, status_code=201)
def create_setting(setting: SettingCreate, db: Session = Depends(get_db)):
    """
    Создать новую настройку
    """
    logger.info("create_setting", key=setting.key, category=setting.category)

    # Проверяем, что настройка не существует
    existing = db.query(Setting).filter(Setting.key == setting.key).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Настройка с ключом '{setting.key}' уже существует"
        )

    # Валидируем значение
    _convert_value(setting.value, setting.value_type)

    # Создаем настройку
    db_setting = Setting(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)

    logger.info("setting_created", key=setting.key)
    return db_setting


@router.put("/settings/{key}", response_model=SettingResponse)
def update_setting(key: str, setting_update: SettingUpdate, db: Session = Depends(get_db)):
    """
    Обновить настройку
    """
    logger.info("update_setting", key=key, updates=setting_update.dict(exclude_unset=True))

    db_setting = db.query(Setting).filter(Setting.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail=f"Настройка '{key}' не найдена")

    update_data = setting_update.dict(exclude_unset=True)

    # Если обновляется значение, валидируем его тип
    if 'value' in update_data:
        _convert_value(update_data['value'], db_setting.value_type)

    # Обновляем поля
    for field, value in update_data.items():
        setattr(db_setting, field, value)

    db.commit()
    db.refresh(db_setting)

    logger.info("setting_updated", key=key)
    return db_setting


@router.delete("/settings/{key}", status_code=204)
def delete_setting(key: str, db: Session = Depends(get_db)):
    """
    Удалить настройку
    """
    logger.info("delete_setting", key=key)

    db_setting = db.query(Setting).filter(Setting.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail=f"Настройка '{key}' не найдена")

    db.delete(db_setting)
    db.commit()

    logger.info("setting_deleted", key=key)


@router.post("/settings/bulk", response_model=List[SettingResponse])
def bulk_update_settings(bulk_update: BulkSettingsUpdate, db: Session = Depends(get_db)):
    """
    Массовое создание/обновление настроек
    """
    logger.info("bulk_update_settings", count=len(bulk_update.settings))

    updated_settings = []

    for setting_data in bulk_update.settings:
        setting_dict = setting_data.dict()
        setting_dict['updated_by'] = bulk_update.updated_by

        # Валидируем значение
        _convert_value(setting_dict['value'], setting_dict['value_type'])

        # Проверяем существование
        existing = db.query(Setting).filter(Setting.key == setting_dict['key']).first()

        if existing:
            # Обновляем
            for field, value in setting_dict.items():
                if field != 'key':  # key не обновляем
                    setattr(existing, field, value)
            updated_settings.append(existing)
        else:
            # Создаем новую
            new_setting = Setting(**setting_dict)
            db.add(new_setting)
            updated_settings.append(new_setting)

    db.commit()

    # Обновляем объекты из БД
    for setting in updated_settings:
        db.refresh(setting)

    logger.info("bulk_update_completed", count=len(updated_settings))
    return updated_settings


@router.get("/settings/category/{category}", response_model=List[SettingResponse])
def get_settings_by_category(category: str, db: Session = Depends(get_db)):
    """
    Получить все настройки определенной категории
    """
    logger.info("get_settings_by_category", category=category)

    settings = db.query(Setting).filter(Setting.category == category).order_by(Setting.key).all()

    if not settings:
        logger.warning("no_settings_found", category=category)

    return settings
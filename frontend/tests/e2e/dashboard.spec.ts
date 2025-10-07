import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('должен правильно загружаться дашборд', async ({ page }) => {
    await page.goto('/');

    // Проверяем заголовок
    await expect(page.locator('h2')).toContainText('Dashboard');

    // Проверяем что есть подзаголовок с описанием
    await expect(page.getByText('Обзор ключевых метрик и показателей эффективности')).toBeVisible();

    // Проверяем статус загрузки данных
    await expect(page.getByText(/Данные загружены|Загрузка.../)).toBeVisible();
  });

  test('должны отображаться карточки метрик', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки данных
    await page.waitForTimeout(2000);

    // Проверяем что есть карточки метрик
    await expect(page.getByText('CAC текущий')).toBeVisible();
    await expect(page.getByText('Активные кампании')).toBeVisible();
    await expect(page.getByText('Конверсии')).toBeVisible();
    await expect(page.getByText('ROAS средний')).toBeVisible();
  });

  test('должна работать кнопка "Создать кампанию"', async ({ page }) => {
    await page.goto('/');

    // Находим и кликаем кнопку "Создать кампанию" в быстрых действиях
    const createButton = page.getByRole('button', { name: 'Создать кампанию' }).first();
    await expect(createButton).toBeVisible();
    await createButton.click();

    // Должна произойти навигация на страницу кампаний
    await expect(page.locator('h1')).toContainText('Кампании');
  });

  test('должна работать кнопка "Обновить данные"', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки страницы
    await page.waitForTimeout(1000);

    // Кликаем кнопку "Обновить данные"
    const refreshButton = page.getByRole('button', { name: 'Обновить данные' });
    await expect(refreshButton).toBeVisible();
    await refreshButton.click();

    // Проверяем что кнопка кликабельна (не проверяем фактическое обновление данных)
    await expect(refreshButton).toBeEnabled();
  });

  test('должна отображаться секция выручки', async ({ page }) => {
    await page.goto('/');

    // Проверяем заголовок секции выручки
    await expect(page.getByText('Выручка за месяц')).toBeVisible();

    // Проверяем прогресс бар
    await expect(page.getByText('Прогресс к цели')).toBeVisible();
  });

  test('должна отображаться секция "Быстрые действия"', async ({ page }) => {
    await page.goto('/');

    // Проверяем заголовок секции
    await expect(page.getByText('Быстрые действия')).toBeVisible();

    // Проверяем описание
    await expect(page.getByText('Основные операции для управления кампаниями')).toBeVisible();

    // Проверяем наличие кнопок
    await expect(page.getByRole('button', { name: 'Создать кампанию' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Обновить данные' })).toBeVisible();
  });

  test('должен корректно отображаться на мобильных устройствах', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone размер
    await page.goto('/');

    // Проверяем что меню-бургер видим на мобильном
    const menuButton = page.getByRole('button', { name: 'Открыть меню' });
    await expect(menuButton).toBeVisible();

    // Кликаем меню и проверяем что оно открывается
    await menuButton.click();
    await expect(page.getByText('DeepCalm')).toBeVisible();
    await expect(page.getByText('Marketing Autopilot')).toBeVisible();

    // Закрываем меню
    const closeButton = page.getByRole('button', { name: 'Закрыть меню' });
    await closeButton.click();

    // Проверяем что контент адаптивен и не растягивается
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible();
  });

  test('должна работать навигация в боковом меню', async ({ page }) => {
    await page.goto('/');

    // Проверяем что мы на дашборде
    await expect(page.getByText('Dashboard')).toBeVisible();

    // Переходим на страницу кампаний
    await page.getByRole('button', { name: /Кампании.*Управление запусками/ }).click();
    await expect(page.locator('h1')).toContainText('Кампании');

    // Переходим на интеграции
    await page.getByRole('button', { name: /Интеграции.*Подключение каналов/ }).click();
    await expect(page.locator('h1')).toContainText('Интеграции');

    // Переходим на AI Analyst
    await page.getByRole('button', { name: /AI Analyst.*Рекомендации AI/ }).click();
    await expect(page.locator('h1')).toContainText('AI Analyst');

    // Возвращаемся на дашборд
    await page.getByRole('button', { name: /Dashboard.*Обзор показателей/ }).click();
    await expect(page.locator('h1')).toContainText('Dashboard');
  });
});
import type { ReactElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from '../Dashboard';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../api/client', () => ({
  analyticsApi: {
    dashboard: vi.fn(),
    dashboardDaily: vi.fn(),
    channelPerformance: vi.fn(),
  },
}));

import { analyticsApi } from '../../api/client';

const renderWithClient = (ui: ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
      },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

const mockDashboard = analyticsApi.dashboard as unknown as vi.Mock;
const mockDashboardDaily = analyticsApi.dashboardDaily as unknown as vi.Mock;
const mockChannelPerformance = analyticsApi.channelPerformance as unknown as vi.Mock;

afterEach(() => {
  mockDashboard.mockReset();
  mockDashboardDaily.mockReset();
  mockChannelPerformance.mockReset();
});

describe('Dashboard', () => {
  it('показывает основные метрики из API', async () => {
    mockDashboard.mockResolvedValueOnce({
      data: {
        total_campaigns: 12,
        active_campaigns: 8,
        paused_campaigns: 4,
        total_budget_rub: 200000,
        total_spent_rub: 120000,
        budget_utilization: 60,
        total_leads: 320,
        total_conversions: 48,
        total_revenue_rub: 450000,
        avg_cac_rub: 375,
        avg_roas: 3.75,
        top_performing_campaign: {
          campaign_id: 'vk-123',
          campaign_title: 'VK Retargeting',
          roas: 4.2,
        },
      },
    });

    mockDashboardDaily.mockResolvedValueOnce({
      data: [
        {
          date: '2025-01-01',
          conversions: 4,
          leads: 10,
          revenue: 14000,
          spend: 3200,
          cac: 800,
          roas: 4.38,
        },
      ],
    });

    mockChannelPerformance.mockResolvedValueOnce({
      data: [
        {
          channel: 'direct',
          channelName: 'Яндекс.Директ',
          spend: 5000,
          leads: 20,
          conversions: 5,
          revenue: 18000,
          cac: 1000,
          roas: 3.6,
          targetCac: 800,
          sparklineData: [],
        },
      ],
    });

    renderWithClient(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('CAC текущий')).toBeInTheDocument();
    });

    // Проверяем основные элементы
    expect(screen.getByText('⚠️ Требуется внимание')).toBeInTheDocument();
    expect(screen.getByText('Маркетинговая панель')).toBeInTheDocument();
    expect(screen.getByText('Ключевые метрики по воронкам и окупаемости рекламы')).toBeInTheDocument();
  });

  it('показывает сообщение о пустых данных', async () => {
    mockDashboard.mockResolvedValueOnce({ data: null });
    mockDashboardDaily.mockResolvedValueOnce({ data: [] });
    mockChannelPerformance.mockResolvedValueOnce({ data: [] });

    renderWithClient(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Пока нет данных для отображения')).toBeInTheDocument();
    });
  });
});

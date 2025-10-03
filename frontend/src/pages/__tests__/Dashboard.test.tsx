import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';

import { Dashboard } from '../Dashboard';

const mockSummary = {
  total_campaigns: 3,
  active_campaigns: 2,
  paused_campaigns: 1,
  total_budget_rub: 150000,
  total_spent_rub: 90000,
  budget_utilization: 60,
  total_leads: 120,
  total_conversions: 40,
  total_revenue_rub: 360000,
  avg_cac_rub: 750,
  avg_roas: 4.0,
  top_performing_campaign: {
    campaign_id: '123',
    campaign_title: 'Лучший результат',
    roas: 5.2,
  },
};

vi.mock('../../api/client', () => ({
  analyticsApi: {
    dashboard: vi.fn(() => Promise.resolve({ data: mockSummary })),
  },
}));

describe('Dashboard', () => {
  it('отображает ключевые метрики из API', async () => {
    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <Dashboard />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('2 активных, 1 на паузе')).toBeInTheDocument();
    expect(screen.getByText(/90.*₽/)).toBeInTheDocument();
    expect(screen.getByText('120 / 40')).toBeInTheDocument();
    expect(screen.getByText(/Лучший результат/)).toBeInTheDocument();
  });
});

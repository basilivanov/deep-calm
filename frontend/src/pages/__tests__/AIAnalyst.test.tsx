import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AIAnalyst } from '../AIAnalyst';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('AIAnalyst', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    mockFetch.mockClear();
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AIAnalyst />
      </QueryClientProvider>
    );
  };

  it('renders page title and description', () => {
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      })
    );

    renderComponent();

    expect(screen.getByText('🤖 AI Analyst')).toBeInTheDocument();
    expect(screen.getByText('Анализ кампаний и консультации по performance маркетингу')).toBeInTheDocument();
  });

  it('loads and displays campaigns', async () => {
    const mockCampaigns = {
      items: [
        { id: 1, title: 'Test Campaign', status: 'active', sku: 'TEST-001' },
        { id: 2, title: 'Another Campaign', status: 'paused', sku: 'TEST-002' },
      ],
    };

    mockFetch.mockImplementation((url: string) => {
      if (url === '/api/v1/campaigns') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCampaigns),
        });
      }
      if (url === '/api/v1/analyst/health') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok', message: 'Ready' }),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Campaign (TEST-001) - active')).toBeInTheDocument();
      expect(screen.getByText('Another Campaign (TEST-002) - paused')).toBeInTheDocument();
    });
  });

  it('shows health status', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url === '/api/v1/campaigns') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ items: [] }),
        });
      }
      if (url === '/api/v1/analyst/health') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            message: 'AI service is ready',
            settings: { model: 'gpt-4', temperature: 0.3, max_tokens: 2000 }
          }),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Статус AI Сервиса')).toBeInTheDocument();
      expect(screen.getByText('AI service is ready')).toBeInTheDocument();
      expect(screen.getByText(/Модель: gpt-4/)).toBeInTheDocument();
    });
  });

  it('enables analyze button when campaign is selected', async () => {
    const mockCampaigns = {
      items: [
        { id: 1, title: 'Test Campaign', status: 'active', sku: 'TEST-001' },
      ],
    };

    mockFetch.mockImplementation((url: string) => {
      if (url === '/api/v1/campaigns') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCampaigns),
        });
      }
      if (url === '/api/v1/analyst/health') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok' }),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderComponent();

    await waitFor(() => {
      const select = screen.getByDisplayValue('-- Выберите кампанию --');
      fireEvent.change(select, { target: { value: '1' } });
    });

    expect(screen.getByText('🚀 Анализировать кампанию')).toBeInTheDocument();
  });

  it('shows analysis results after successful analysis', async () => {
    const mockCampaigns = {
      items: [
        { id: 1, title: 'Test Campaign', status: 'active', sku: 'TEST-001' },
      ],
    };

    const mockAnalysisResult = {
      campaign_id: 1,
      analysis: 'This campaign is performing well...',
      metrics: {
        roas: 3.5,
        cac: 2500,
        conversion_rate: 2.1,
        total_leads: 150,
        total_conversions: 25,
      },
      recommendations: ['Increase budget', 'Test new creatives'],
      generated_at: '2024-01-01T12:00:00Z',
    };

    mockFetch.mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/campaigns') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCampaigns),
        });
      }
      if (url === '/api/v1/analyst/health') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok' }),
        });
      }
      if (url === '/api/v1/analyst/analyze/1' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAnalysisResult),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderComponent();

    await waitFor(() => {
      const select = screen.getByDisplayValue('-- Выберите кампанию --');
      fireEvent.change(select, { target: { value: '1' } });
    });

    const analyzeButton = screen.getByText('🚀 Анализировать кампанию');
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('This campaign is performing well...')).toBeInTheDocument();
      expect(screen.getByText(/ROAS:.*3.5/)).toBeInTheDocument();
      expect(screen.getByText(/CAC:.*2500 ₽/)).toBeInTheDocument();
      expect(screen.getByText('Increase budget')).toBeInTheDocument();
      expect(screen.getByText('Test new creatives')).toBeInTheDocument();
    });
  });

  it('shows quick examples section', () => {
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      })
    );

    renderComponent();

    expect(screen.getByText('💡 Примеры вопросов')).toBeInTheDocument();
    expect(screen.getByText('Как снизить CAC для массажа?')).toBeInTheDocument();
    expect(screen.getByText('Лучшие каналы для массажных салонов?')).toBeInTheDocument();
    expect(screen.getByText('Как готовиться к новогодним праздникам?')).toBeInTheDocument();
  });
});
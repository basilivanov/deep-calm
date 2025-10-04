import type { ReactElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AIAnalyst } from '../AIAnalyst';

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

describe('AIAnalyst', () => {
  const fetchMock = vi.fn();
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchMock.mockReset();
    fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(fetchMock as unknown as typeof fetch);
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it('подгружает кампании и отображает статус сервиса', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [
            { id: 1, title: 'VK Massage', status: 'active', sku: 'RELAX-60' },
            { id: 2, title: 'Yandex Direct', status: 'paused', sku: 'DEEP-90' },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'ok',
          message: 'Готов к анализу',
          settings: {
            model: 'gpt-4o-mini',
            temperature: 0.7,
            max_tokens: 1200,
          },
        }),
      });

    renderWithClient(<AIAnalyst />);

    await waitFor(() => {
      expect(screen.getByText('Готов к анализу')).toBeInTheDocument();
    });

    const select = await screen.findByRole('combobox');
    await userEvent.selectOptions(select, '1');

    expect((select as HTMLSelectElement).value).toBe('1');
    expect(screen.getByText('VK Massage (RELAX-60) - active')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/campaigns');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/analyst/health');
  });

  it('показывает UI даже при ошибке API', async () => {
    fetchMock.mockResolvedValue({ ok: false, json: async () => ({}) });

    renderWithClient(<AIAnalyst />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Спросите что-то о маркетинге...')).toBeInTheDocument();
    });
  });
});

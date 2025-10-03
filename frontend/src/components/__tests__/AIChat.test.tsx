import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AIChat } from '../AIChat';
import { vi } from 'vitest';

describe('AIChat', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('показывает приветственное сообщение', () => {
    render(<AIChat campaignId={1} campaignTitle="Пробная кампания" />);

    expect(
      screen.getByText(/готов проанализировать кампанию "Пробная кампания"/i)
    ).toBeInTheDocument();
  });

  it('отправляет сообщение и отображает ответ ассистента', async () => {
    const user = userEvent.setup();

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ response: 'Вот рекомендации по оптимизации.' }),
      }) as unknown as typeof fetch
    );

    render(<AIChat />);

    const textarea = screen.getByPlaceholderText('Спросите что-то о маркетинге...');
    await user.type(textarea, 'Как снизить CAC?');
    await user.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/analyst/chat',
        expect.objectContaining({ method: 'POST' })
      );
      expect(screen.getByText('Как снизить CAC?')).toBeInTheDocument();
      expect(screen.getByText('Вот рекомендации по оптимизации.')).toBeInTheDocument();
    });
  });
});

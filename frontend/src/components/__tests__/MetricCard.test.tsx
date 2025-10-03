import { render, screen } from '@testing-library/react';
import { MetricCard } from '../MetricCard';
import { TrendingUp } from 'lucide-react';

describe('MetricCard', () => {
  it('отображает заголовок, значение и подзаголовок', () => {
    render(
      <MetricCard
        title="Выручка"
        value="1 000 ₽"
        subtitle="ROAS 4.2"
        icon={<TrendingUp data-testid="metric-icon" />}
      />
    );

    expect(screen.getByText('Выручка')).toBeInTheDocument();
    expect(screen.getByText('1 000 ₽')).toBeInTheDocument();
    expect(screen.getByText('ROAS 4.2')).toBeInTheDocument();
    expect(screen.getByTestId('metric-icon')).toBeInTheDocument();
  });

  it('отображает тренд', () => {
    render(
      <MetricCard
        title="Лиды"
        value="250"
        trend={{ value: 12, isPositive: true }}
      />
    );

    expect(screen.getByText('↑ 12%')).toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import { MetricCard } from '../MetricCard';

describe('MetricCard', () => {
  it('отображает заголовок и значение', () => {
    render(<MetricCard title="Выручка" value="100 ₽" />);

    expect(screen.getByText('Выручка')).toBeInTheDocument();
    expect(screen.getByText('100 ₽')).toBeInTheDocument();
  });

  it('показывает подзаголовок и тренд', () => {
    render(
      <MetricCard
        title="CAC"
        value="1 200 ₽"
        subtitle="из 50 000 ₽ (60%)"
        trend={{ value: 15, isPositive: true }}
      />
    );

    expect(screen.getByText('из 50 000 ₽ (60%)')).toBeInTheDocument();
    expect(screen.getByText('▲ 15%')).toBeInTheDocument();
  });
});

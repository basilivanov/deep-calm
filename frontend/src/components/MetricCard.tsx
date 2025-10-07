import type { ReactNode } from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function MetricCard({ title, value, subtitle, icon, trend }: MetricCardProps) {
  return (
    <Card className="h-full">
      <CardHeader className="flex items-center justify-between pb-1">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-dc-neutral">
            {title}
          </p>
        </div>
        {icon && (
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-dc-border bg-dc-bg text-dc-primary">
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-3 pt-5">
        <div className="text-3xl font-semibold leading-tight text-dc-ink">
          {value}
        </div>
        {subtitle && (
          <p className="text-sm text-dc-neutral-600">
            {subtitle}
          </p>
        )}
        {trend && (
          <p className={`mt-3 text-xs font-medium ${trend.isPositive ? 'text-dc-success-600' : 'text-dc-danger-500'}`}>
            {trend.isPositive ? '▲' : '▼'} {Math.abs(trend.value)}%
          </p>
        )}
      </CardContent>
    </Card>
  );
}

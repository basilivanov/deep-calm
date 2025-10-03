import type { ReactNode } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';

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
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-dc-primary">
          {title}
        </CardTitle>
        {icon && <div className="text-dc-accent">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-dc-ink">
          {value}
        </div>
        {subtitle && (
          <p className="text-xs text-dc-primary/60 mt-1">
            {subtitle}
          </p>
        )}
        {trend && (
          <p className={`text-xs mt-1 ${trend.isPositive ? 'text-dc-success' : 'text-dc-error'}`}>
            {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
          </p>
        )}
      </CardContent>
    </Card>
  );
}

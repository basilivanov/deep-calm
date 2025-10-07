import { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';

interface RevenueSpeedometerProps {
  current: number; // текущая выручка за месяц
  target: number;  // целевая выручка из настроек
  label?: string;
}

export function RevenueSpeedometer({
  current,
  target,
  label = "Выручка за месяц"
}: RevenueSpeedometerProps) {
  const percentage = useMemo(() => {
    return Math.min((current / target) * 100, 100);
  }, [current, target]);

  const getColor = (percent: number) => {
    if (percent >= 90) return '#22c55e'; // green
    if (percent >= 70) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  const formatRub = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const radius = 80;
  const strokeWidth = 8;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

  return (
    <Card className="flex h-full flex-col items-center text-center">
      <CardHeader className="flex flex-col items-center gap-2 pb-0 text-center">
        <CardTitle className="text-base font-semibold text-dc-ink">
          {label}
        </CardTitle>
        <p className="text-xs uppercase tracking-[0.22em] text-dc-neutral">Достижение цели</p>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col items-center justify-center gap-6">
        <div className="relative">
          <svg
            height={radius * 2}
            width={radius * 2}
            className="transform -rotate-90"
          >
          {/* Background circle */}
          <circle
            stroke="#e7dbd1"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          {/* Progress circle */}
          <circle
            stroke={getColor(percentage)}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
            style={{
              strokeDashoffset: 0,
              transition: 'stroke-dasharray 0.5s ease-in-out',
            }}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-3xl font-bold text-dc-ink">
            {percentage.toFixed(0)}%
          </div>
          <div className="text-sm text-dc-neutral-600">
            от цели
          </div>
        </div>
      </div>

        <div>
          <div className="text-xl font-semibold text-dc-ink">
            {formatRub(current)}
          </div>
          <div className="text-sm text-dc-neutral-500">
            из {formatRub(target)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

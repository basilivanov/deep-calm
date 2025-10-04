import { cn } from '../../utils/cn';

interface ProgressBarProps {
  value: number; // 0-100
  max?: number;
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  color = 'accent',
  size = 'md',
  showLabel = false,
  label,
  className
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const colorClasses = {
    primary: 'bg-dc-primary-500',
    accent: 'bg-dc-accent-500',
    success: 'bg-dc-success-500',
    warning: 'bg-dc-warning-500',
    danger: 'bg-dc-danger-500'
  };

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  };

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-dc-ink">{label}</span>
          <span className="text-sm text-dc-neutral-600">
            {value.toLocaleString('ru-RU')} / {max.toLocaleString('ru-RU')}
          </span>
        </div>
      )}
      <div className={cn(
        'w-full bg-dc-warm-300 rounded-full overflow-hidden',
        sizeClasses[size]
      )}>
        <div
          className={cn(
            'h-full transition-all duration-300 ease-out rounded-full',
            colorClasses[color]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
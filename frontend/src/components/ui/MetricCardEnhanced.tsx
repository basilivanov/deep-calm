import React from 'react'
import { GlassCard } from './GlassCard'
import { ProgressRing } from './ProgressRing'
import { Sparkline } from './Sparkline'
import { StatusPill } from './StatusPill'
import { type LucideProps } from 'lucide-react'

interface MetricCardEnhancedProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: React.ComponentType<LucideProps>
  trend?: {
    data: number[]
    isPositive: boolean
    label?: string
  }
  progress?: {
    value: number
    max: number
    label?: string
  }
  status?: {
    type: 'success' | 'warning' | 'error' | 'neutral' | 'active' | 'inactive'
    text: string
  }
  variant?: 'default' | 'glass' | 'gradient' | 'warm'
  onClick?: () => void
  children?: React.ReactNode
  className?: string
}

export function MetricCardEnhanced({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  progress,
  status,
  variant = 'glass',
  onClick,
  children,
  className
}: MetricCardEnhancedProps) {
  const statusColors = {
    success: { primary: '#22c55e', secondary: '#dcfce7', accent: '#15803d' },
    warning: { primary: '#f59e0b', secondary: '#fef3c7', accent: '#b45309' },
    error: { primary: '#ef4444', secondary: '#fee2e2', accent: '#b91c1c' },
    neutral: { primary: '#828282', secondary: '#f3f4f6', accent: '#515151' },
    active: { primary: '#A67C52', secondary: '#f9f4ee', accent: '#7d5e3e' },
    inactive: { primary: '#828282', secondary: '#f3f4f6', accent: '#515151' }
  }

  const colors = status ? statusColors[status.type] : statusColors.neutral

  return (
    <GlassCard
      variant={variant}
      className={`h-full ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center space-x-3">
          {Icon && (
            <div
              className="p-3 rounded-xl border border-dc-warm-300/60"
              style={{ backgroundColor: colors.secondary }}
            >
              <Icon
                className="h-5 w-5"
                style={{ color: colors.accent }}
              />
            </div>
          )}
          <div>
            <h3 className="text-sm font-medium text-dc-neutral-600 uppercase tracking-wide">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-dc-neutral-500 mt-1">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        {status && (
          <StatusPill
            status={status.type}
            text={status.text}
            size="sm"
            variant="soft"
          />
        )}
      </div>

      {/* Main content */}
      <div className="space-y-6">
        {/* Value and progress */}
        <div className="flex items-end justify-between">
          <div className="flex-1">
            <div
              className="text-4xl font-bold leading-none"
              style={{ color: colors.accent }}
            >
              {value}
            </div>

            {/* Trend */}
            {trend && (
              <div className="flex items-center space-x-3 mt-3">
                <Sparkline
                  data={trend.data}
                  width={80}
                  height={24}
                  color={trend.isPositive ? '#22c55e' : '#ef4444'}
                  showDots={false}
                  animate={true}
                />
                <div className="flex items-center space-x-1">
                  <span
                    className={`text-sm font-medium ${
                      trend.isPositive ? 'text-dc-success-600' : 'text-dc-danger-500'
                    }`}
                  >
                    {trend.isPositive ? '↗' : '↘'}
                  </span>
                  {trend.label && (
                    <span className="text-xs text-dc-neutral-500">
                      {trend.label}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Progress ring */}
          {progress && (
            <div className="flex-shrink-0 ml-4">
              <ProgressRing
                value={progress.value}
                max={progress.max}
                size={90}
                strokeWidth={6}
                gradientFrom={colors.primary}
                gradientTo={colors.accent}
                labelText={progress.label}
                showLabel={true}
              />
            </div>
          )}
        </div>

        {/* Additional content */}
        {children && (
          <div className="pt-4 border-t border-dc-warm-300/40">
            {children}
          </div>
        )}
      </div>
    </GlassCard>
  )
}
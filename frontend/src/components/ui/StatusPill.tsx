import React from 'react'
import { clsx } from 'clsx'

interface StatusPillProps {
  status: 'success' | 'warning' | 'error' | 'neutral' | 'active' | 'inactive'
  text: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'solid' | 'outline' | 'soft'
  className?: string
}

export function StatusPill({
  status,
  text,
  size = 'md',
  variant = 'soft',
  className
}: StatusPillProps) {
  const statusConfig = {
    success: {
      colors: {
        solid: 'bg-dc-success-500 text-white border-dc-success-600',
        outline: 'border-dc-success-500 text-dc-success-700 bg-transparent',
        soft: 'bg-dc-success-100 text-dc-success-700 border-dc-success-200'
      },
      dot: 'bg-dc-success-500'
    },
    warning: {
      colors: {
        solid: 'bg-dc-warning-500 text-white border-dc-warning-600',
        outline: 'border-dc-warning-500 text-dc-warning-700 bg-transparent',
        soft: 'bg-dc-warning-100 text-dc-warning-700 border-dc-warning-200'
      },
      dot: 'bg-dc-warning-500'
    },
    error: {
      colors: {
        solid: 'bg-dc-danger-500 text-white border-dc-danger-600',
        outline: 'border-dc-danger-500 text-dc-danger-700 bg-transparent',
        soft: 'bg-dc-danger-100 text-dc-danger-700 border-dc-danger-200'
      },
      dot: 'bg-dc-danger-500'
    },
    active: {
      colors: {
        solid: 'bg-dc-accent-500 text-white border-dc-accent-600',
        outline: 'border-dc-accent-500 text-dc-accent-700 bg-transparent',
        soft: 'bg-dc-accent-100 text-dc-accent-700 border-dc-accent-200'
      },
      dot: 'bg-dc-accent-500'
    },
    inactive: {
      colors: {
        solid: 'bg-dc-neutral-500 text-white border-dc-neutral-600',
        outline: 'border-dc-neutral-500 text-dc-neutral-700 bg-transparent',
        soft: 'bg-dc-neutral-100 text-dc-neutral-700 border-dc-neutral-200'
      },
      dot: 'bg-dc-neutral-500'
    },
    neutral: {
      colors: {
        solid: 'bg-dc-primary-500 text-white border-dc-primary-600',
        outline: 'border-dc-primary-500 text-dc-primary-700 bg-transparent',
        soft: 'bg-dc-primary-100 text-dc-primary-700 border-dc-primary-200'
      },
      dot: 'bg-dc-primary-500'
    }
  }

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base'
  }

  const config = statusConfig[status]
  const colorClasses = config.colors[variant]

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-2 rounded-full border font-medium transition-all duration-200',
        sizeClasses[size],
        colorClasses,
        'hover:scale-105',
        className
      )}
    >
      <span
        className={clsx(
          'w-2 h-2 rounded-full animate-pulse',
          config.dot
        )}
      />
      {text}
    </span>
  )
}
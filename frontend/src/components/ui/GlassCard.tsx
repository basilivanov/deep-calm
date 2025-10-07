import React from 'react'
import { Card } from './Card'
import { clsx } from 'clsx'

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'glass' | 'gradient' | 'warm'
  intensity?: 'low' | 'medium' | 'high'
  hover?: boolean
}

export function GlassCard({
  children,
  className,
  variant = 'glass',
  intensity = 'medium',
  hover = true,
  ...props
}: GlassCardProps) {
  const baseClasses = "relative overflow-hidden transition-all duration-300"

  const variantClasses = {
    default: "bg-dc-bg-secondary border border-dc-border",
    glass: clsx(
      "backdrop-blur-md border border-dc-warm-300/40",
      intensity === 'low' && "bg-dc-bg-secondary/70",
      intensity === 'medium' && "bg-dc-bg-secondary/80",
      intensity === 'high' && "bg-dc-bg-secondary/90"
    ),
    gradient: "bg-gradient-to-br from-dc-bg-secondary to-dc-warm-100 border border-dc-warm-300/50",
    warm: "bg-gradient-to-br from-dc-warm-50 to-dc-warm-100 border border-dc-accent-200/60 shadow-lg shadow-dc-accent-100/30"
  }

  const hoverClasses = hover ? clsx(
    "hover:scale-[1.02] hover:shadow-xl hover:-translate-y-1",
    variant === 'glass' && "hover:bg-dc-bg-secondary/85 hover:border-dc-warm-400/50",
    variant === 'warm' && "hover:border-dc-accent-300/70 hover:shadow-dc-accent-200/40",
    "hover:shadow-[0_20px_40px_-12px_rgba(107,78,61,0.25)]"
  ) : ""

  return (
    <div
      className={clsx(
        baseClasses,
        variantClasses[variant],
        hoverClasses,
        "rounded-2xl p-6 shadow-lg shadow-dc-primary/5",
        className
      )}
      {...props}
    >
      {/* Декоративные элементы для warm варианта */}
      {variant === 'warm' && (
        <>
          <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-dc-accent-400 to-transparent opacity-50" />
          <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-dc-accent-400 to-transparent opacity-50" />
        </>
      )}

      {/* Gradient overlay для gradient варианта */}
      {variant === 'gradient' && (
        <div className="absolute inset-0 bg-gradient-to-br from-dc-accent-500/5 to-dc-primary-600/5 pointer-events-none" />
      )}

      {children}
    </div>
  )
}
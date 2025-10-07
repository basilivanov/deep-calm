import React, { useMemo } from 'react'

interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  color?: string
  strokeWidth?: number
  showDots?: boolean
  animate?: boolean
  className?: string
}

export function Sparkline({
  data,
  width = 100,
  height = 30,
  color = '#A67C52', // dc-accent
  strokeWidth = 2,
  showDots = false,
  animate = true,
  className = ''
}: SparklineProps) {
  const { pathData, dots } = useMemo(() => {
    if (!data || data.length === 0) {
      return { pathData: '', dots: [] }
    }

    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width
      const y = height - ((value - min) / range) * height
      return { x, y, value }
    })

    const pathData = points.reduce((path, point, index) => {
      const command = index === 0 ? 'M' : 'L'
      return `${path} ${command} ${point.x} ${point.y}`
    }, '')

    return { pathData, dots: points }
  }, [data, width, height])

  if (!data || data.length === 0) {
    return (
      <div
        className={`inline-flex items-center justify-center bg-dc-warm-100/50 rounded ${className}`}
        style={{ width, height }}
      >
        <div className="text-xs text-dc-neutral-400">—</div>
      </div>
    )
  }

  const gradientId = `sparkline-gradient-${Math.random().toString(36).substr(2, 9)}`

  return (
    <div className={`inline-block ${className}`}>
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity={0.8} />
            <stop offset="100%" stopColor={color} stopOpacity={1} />
          </linearGradient>
        </defs>

        {/* Main path */}
        <path
          d={pathData}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          className={animate ? "transition-all duration-500 ease-out" : ""}
          style={{
            filter: `drop-shadow(0 0 3px ${color}40)`
          }}
        />

        {/* Dots at each point */}
        {showDots && dots.map((dot, index) => (
          <circle
            key={index}
            cx={dot.x}
            cy={dot.y}
            r={strokeWidth}
            fill={color}
            className={animate ? `transition-all duration-500 ease-out delay-${index * 50}` : ""}
            style={{
              filter: `drop-shadow(0 0 2px ${color}60)`
            }}
          />
        ))}
      </svg>
    </div>
  )
}
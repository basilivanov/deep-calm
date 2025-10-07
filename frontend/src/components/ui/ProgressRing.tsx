import { useMemo } from 'react'

interface ProgressRingProps {
  value: number
  max: number
  size?: number
  strokeWidth?: number
  gradientFrom?: string
  gradientTo?: string
  labelText?: string
  showLabel?: boolean
  animate?: boolean
  className?: string
}

export function ProgressRing({
  value,
  max,
  size = 120,
  strokeWidth = 8,
  gradientFrom = '#A67C52', // dc-accent
  gradientTo = '#6B4E3D',   // dc-primary
  labelText,
  showLabel = true,
  animate = true,
  className = ''
}: ProgressRingProps) {
  const { percentage, strokeDasharray, strokeDashoffset } = useMemo(() => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
    const radius = (size - strokeWidth) / 2
    const circumference = radius * 2 * Math.PI
    const strokeDasharray = circumference
    const strokeDashoffset = circumference - (percentage / 100) * circumference

    return { percentage, strokeDasharray, strokeDashoffset }
  }, [value, max, size, strokeWidth])

  const center = size / 2
  const radius = (size - strokeWidth) / 2
  const gradientId = `progress-gradient-${Math.random().toString(36).substr(2, 9)}`

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={gradientFrom} />
            <stop offset="100%" stopColor={gradientTo} />
          </linearGradient>
        </defs>

        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-dc-warm-300/60"
        />

        {/* Progress circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={animate ? "transition-all duration-1000 ease-out" : ""}
          style={{
            filter: 'drop-shadow(0 0 6px rgba(166, 124, 82, 0.3))'
          }}
        />
      </svg>

      {/* Center content */}
      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-bold text-dc-primary">
            {Math.round(percentage)}%
          </div>
          {labelText && (
            <div className="text-xs text-dc-neutral-600 mt-1 text-center max-w-[80%]">
              {labelText}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface SparkLineProps {
  data: Array<{ value: number; date?: string }>;
  color?: string;
  height?: number;
  strokeWidth?: number;
}

export function SparkLine({
  data,
  color = 'var(--dc-accent)',
  height = 32,
  strokeWidth = 2
}: SparkLineProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={strokeWidth}
          dot={false}
          activeDot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
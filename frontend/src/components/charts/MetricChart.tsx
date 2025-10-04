import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface MetricChartProps {
  data: Array<{
    date: string;
    cac?: number;
    roas?: number;
    conversions?: number;
    revenue?: number;
    spend?: number;
  }>;
  metrics: ('cac' | 'roas' | 'conversions' | 'revenue' | 'spend')[];
  height?: number;
  title?: string;
}

const metricConfig = {
  cac: {
    key: 'cac',
    name: 'CAC',
    color: '#ef4444', // dc-danger-500
    formatter: (value: number) => `${value.toFixed(0)}₽`
  },
  roas: {
    key: 'roas',
    name: 'ROAS',
    color: '#22c55e', // dc-success-500
    formatter: (value: number) => value.toFixed(1)
  },
  conversions: {
    key: 'conversions',
    name: 'Конверсии',
    color: '#6B4E3D', // dc-primary-500
    formatter: (value: number) => value.toString()
  },
  revenue: {
    key: 'revenue',
    name: 'Выручка',
    color: '#A67C52', // dc-accent-500
    formatter: (value: number) => `${(value / 1000).toFixed(0)}к₽`
  },
  spend: {
    key: 'spend',
    name: 'Расходы',
    color: '#f59e0b', // dc-warning-500
    formatter: (value: number) => `${(value / 1000).toFixed(0)}к₽`
  }
};

export function MetricChart({ data, metrics, height = 300, title }: MetricChartProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="w-full">
      {title && (
        <h3 className="text-lg font-semibold text-dc-ink mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7dbd1" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="#6f665d"
            fontSize={12}
          />
          <YAxis stroke="#6f665d" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#f7f5f2',
              border: '1px solid #d0c5b9',
              borderRadius: '8px',
              color: '#262626'
            }}
            labelFormatter={(label) => formatDate(label)}
            formatter={(value: number, name: string) => {
              const metric = Object.values(metricConfig).find(m => m.name === name);
              return metric ? metric.formatter(value) : value;
            }}
          />
          <Legend />
          {metrics.map(metricKey => {
            const config = metricConfig[metricKey];
            return (
              <Line
                key={config.key}
                type="monotone"
                dataKey={config.key}
                stroke={config.color}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name={config.name}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
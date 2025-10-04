import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ProgressBar } from './ProgressBar';
import { SparkLine } from './SparkLine';

interface ChannelData {
  channel: string;
  channelName: string;
  spend: number;
  leads: number;
  conversions: number;
  revenue: number;
  cac: number;
  roas: number;
  targetCac: number;
  sparklineData: Array<{ value: number; date: string }>;
}

interface ChannelPerformanceProps {
  data: ChannelData[];
  title?: string;
}

const channelConfig = {
  vk: { name: 'VK Реклама', color: '#4680C2' },
  direct: { name: 'Яндекс.Директ', color: '#FFCC00' },
  avito: { name: 'Avito', color: '#00A956' }
};

export function ChannelPerformance({ data, title = "Эффективность каналов" }: ChannelPerformanceProps) {
  const formatRub = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);
  };


  const getCACStatus = (cac: number, targetCac: number) => {
    if (cac <= targetCac) return 'success';
    if (cac <= targetCac * 1.2) return 'warning';
    return 'danger';
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-dc-ink">{title}</h3>

      {/* CAC по каналам - график */}
      <div className="bg-white rounded-lg border border-dc-warm-300 p-6">
        <h4 className="text-md font-medium text-dc-ink mb-4">CAC по каналам</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7dbd1" />
            <XAxis
              dataKey="channelName"
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
              formatter={(value: number) => [`${value.toFixed(0)}₽`, 'CAC']}
            />
            <Bar dataKey="cac" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => {
                const status = getCACStatus(entry.cac, entry.targetCac);
                const color = status === 'success' ? '#22c55e' :
                           status === 'warning' ? '#f59e0b' : '#ef4444';
                return <Cell key={`cell-${index}`} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Детальная таблица */}
      <div className="bg-white rounded-lg border border-dc-warm-300 overflow-hidden">
        <div className="px-6 py-4 border-b border-dc-warm-300">
          <h4 className="text-md font-medium text-dc-ink">Детальная статистика</h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dc-warm-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  Канал
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  Расходы
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  Лиды
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  Конверсии
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  CAC
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  ROAS
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dc-ink uppercase tracking-wider">
                  Тренд CAC
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-dc-warm-200">
              {data.map((channel) => (
                <tr key={channel.channel} className="hover:bg-dc-warm-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div
                        className="w-3 h-3 rounded-full mr-3"
                        style={{ backgroundColor: channelConfig[channel.channel as keyof typeof channelConfig]?.color || '#828282' }}
                      />
                      <span className="text-sm font-medium text-dc-ink">
                        {channel.channelName}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-dc-ink">
                    {formatRub(channel.spend)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-dc-ink">
                    {channel.leads}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-dc-ink">
                    {channel.conversions}
                    <div className="w-16 mt-1">
                      <ProgressBar
                        value={channel.conversions}
                        max={channel.leads}
                        size="sm"
                        color={channel.conversions / channel.leads >= 0.1 ? 'success' : 'warning'}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-dc-ink">
                      {formatRub(channel.cac)}
                    </span>
                    <div className="w-20 mt-1">
                      <ProgressBar
                        value={channel.cac}
                        max={channel.targetCac * 1.5}
                        size="sm"
                        color={getCACStatus(channel.cac, channel.targetCac)}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${
                      channel.roas >= 5 ? 'text-dc-success-700' :
                      channel.roas >= 3 ? 'text-dc-warning-700' :
                      'text-dc-danger-700'
                    }`}>
                      {channel.roas.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-24 h-8">
                      <SparkLine
                        data={channel.sparklineData}
                        color={getCACStatus(channel.cac, channel.targetCac) === 'success' ? '#22c55e' : '#ef4444'}
                        height={32}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
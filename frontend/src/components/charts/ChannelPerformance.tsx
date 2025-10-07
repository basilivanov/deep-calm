import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ChannelPerformanceItem } from '../../api/client';
import { ProgressBar } from './ProgressBar';
import { SparkLine } from './SparkLine';

type ChannelData = ChannelPerformanceItem;

interface ChannelPerformanceProps {
  data: ChannelData[];
  title?: string;
}

const channelConfig = {
  vk: { name: 'VK Реклама', color: '#4680C2' },
  direct: { name: 'Яндекс.Директ', color: '#FFCC00' },
  avito: { name: 'Avito', color: '#00A956' }
};

export function ChannelPerformance({ data, title }: ChannelPerformanceProps) {
  const formatRub = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);
  };


  const getCACStatus = (cac: number | null | undefined, targetCac: number | null | undefined) => {
    if (cac == null || targetCac == null || targetCac === 0) return 'warning';
    if (cac <= targetCac) return 'success';
    if (cac <= targetCac * 1.2) return 'warning';
    return 'danger';
  };
  return (
    <div className="space-y-6">
      {title && <h3 className="text-lg font-semibold text-dc-ink">{title}</h3>}

      <div className="rounded-2xl border border-dc-border/60 bg-dc-bg px-6 py-5 shadow-sm">
        <h4 className="mb-4 text-sm font-medium uppercase tracking-[0.18em] text-dc-neutral">CAC по каналам</h4>
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

      <div className="overflow-hidden rounded-2xl border border-dc-border/60 bg-dc-bg shadow-sm">
        <div className="border-b border-dc-border/60 px-4 py-4 sm:px-6">
          <h4 className="text-sm font-medium uppercase tracking-[0.18em] text-dc-neutral">Детальная статистика</h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px]">
            <thead className="bg-dc-bg-secondary">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  Канал
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  Расходы
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  Лиды
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  Конверсии
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  CAC
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  ROAS
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-dc-neutral-600 sm:px-6">
                  Тренд CAC
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dc-border/40 bg-dc-bg">
              {data.map((channel) => {
                const spend = channel.spend ?? 0;
                const leads = channel.leads ?? 0;
                const conversions = channel.conversions ?? 0;
                const cac = channel.cac ?? 0;
                const targetCac = channel.targetCac ?? (cac || 1);
                const roas = channel.roas ?? 0;
                const cacStatus = getCACStatus(channel.cac, channel.targetCac);
                const conversionsRatio = leads > 0 ? conversions / leads : 0;
                const trendColor = cacStatus === 'success' ? '#22c55e' : cacStatus === 'danger' ? '#ef4444' : '#f59e0b';

                return (
                <tr key={channel.channel} className="hover:bg-dc-bg-secondary/70">
                  <td className="whitespace-nowrap px-4 py-4 sm:px-6">
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
                  <td className="whitespace-nowrap px-4 py-4 text-sm text-dc-ink sm:px-6">
                    {formatRub(spend)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-4 text-sm text-dc-ink sm:px-6">
                    {leads}
                  </td>
                  <td className="whitespace-nowrap px-4 py-4 text-sm text-dc-ink sm:px-6">
                    {conversions}
                    <div className="w-16 mt-1">
                      <ProgressBar
                        value={conversions}
                        max={Math.max(leads, 1)}
                        size="sm"
                        color={conversionsRatio >= 0.1 ? 'success' : 'warning'}
                      />
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-4 sm:px-6">
                    <span className="text-sm text-dc-ink">
                      {formatRub(cac)}
                    </span>
                    <div className="w-20 mt-1">
                      <ProgressBar
                        value={cac}
                        max={Math.max(targetCac * 1.5, 1)}
                        size="sm"
                        color={cacStatus}
                      />
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-4 sm:px-6">
                    <span className={`text-sm font-medium ${
                      roas >= 5 ? 'text-dc-success-700' :
                      roas >= 3 ? 'text-dc-warning-700' :
                      'text-dc-danger-700'
                    }`}>
                      {roas != null ? roas.toFixed(1) : '—'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-4 sm:px-6">
                    <div className="w-24 h-8">
                      <SparkLine
                        data={channel.sparklineData}
                        color={trendColor}
                        height={32}
                      />
                    </div>
                  </td>
                </tr>
              );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

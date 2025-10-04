import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Users, DollarSign, Target, AlertTriangle, CheckCircle } from 'lucide-react';
import type { DashboardSummary } from '../api/client';
import { analyticsApi } from '../api/client';
import { MetricCard } from '../components/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricChart } from '../components/charts/MetricChart';
import { RevenueSpeedometer } from '../components/charts/RevenueSpeedometer';
import { ChannelPerformance } from '../components/charts/ChannelPerformance';

export function Dashboard() {
  const { data: summary, isLoading } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const response = await analyticsApi.dashboard();
      return response.data;
    },
    refetchInterval: 30000, // Обновление каждые 30 сек
  });

  // Дополнительные запросы для графиков
  const { data: dailyMetrics } = useQuery({
    queryKey: ['daily-metrics'],
    queryFn: async () => {
      // TODO: реальный API endpoint /api/v1/analytics/daily?range=30d
      return generateMockDailyData();
    },
    refetchInterval: 300000, // 5 минут
  });

  const { data: channelData } = useQuery({
    queryKey: ['channel-performance'],
    queryFn: async () => {
      // TODO: реальный API endpoint /api/v1/analytics/channels?range=30d
      return generateMockChannelData();
    },
    refetchInterval: 300000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">Загрузка...</div>
      </div>
    );
  }

  if (!summary) {
    return <div>Нет данных</div>;
  }

  const formatRub = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);
  };

  // Генерация моковых данных для демонстрации (до подключения реального API)
  const generateMockDailyData = () => {
    const data = [];
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      data.push({
        date: date.toISOString().split('T')[0],
        cac: 450 + Math.random() * 200 - 100, // CAC около 450₽ ± 100₽
        roas: 4.5 + Math.random() * 2 - 1,    // ROAS около 4.5 ± 1
        conversions: Math.floor(Math.random() * 8) + 2, // 2-10 конверсий
        revenue: 15000 + Math.random() * 10000 - 5000,  // выручка 10-20к
        spend: 3000 + Math.random() * 2000 - 1000       // расходы 2-5к
      });
    }
    return data;
  };

  const generateMockChannelData = () => {
    return [
      {
        channel: 'vk',
        channelName: 'VK Реклама',
        spend: 45000,
        leads: 120,
        conversions: 18,
        revenue: 63000,
        cac: 375,
        roas: 1.4,
        targetCac: 500,
        sparklineData: Array.from({length: 7}, (_, i) => ({
          value: 350 + Math.random() * 100,
          date: new Date(Date.now() - (6-i) * 24 * 60 * 60 * 1000).toISOString()
        }))
      },
      {
        channel: 'direct',
        channelName: 'Яндекс.Директ',
        spend: 32000,
        leads: 85,
        conversions: 15,
        revenue: 52500,
        cac: 376,
        roas: 1.64,
        targetCac: 500,
        sparklineData: Array.from({length: 7}, (_, i) => ({
          value: 380 + Math.random() * 80,
          date: new Date(Date.now() - (6-i) * 24 * 60 * 60 * 1000).toISOString()
        }))
      },
      {
        channel: 'avito',
        channelName: 'Avito',
        spend: 28000,
        leads: 95,
        conversions: 12,
        revenue: 42000,
        cac: 295,
        roas: 1.5,
        targetCac: 500,
        sparklineData: Array.from({length: 7}, (_, i) => ({
          value: 290 + Math.random() * 60,
          date: new Date(Date.now() - (6-i) * 24 * 60 * 60 * 1000).toISOString()
        }))
      }
    ];
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-dc-primary">
          Dashboard
        </h1>
        <p className="text-dc-primary/70 mt-1">
          Обзор всех кампаний и метрик
        </p>
      </div>

      {/* Основные метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="CAC текущий"
          value={summary.avg_cac_rub ? formatRub(summary.avg_cac_rub) : '—'}
          subtitle={
            summary.avg_cac_rub
              ? summary.avg_cac_rub <= 500
                ? '✅ В пределах нормы'
                : '⚠️ Выше целевого'
              : 'Нет данных'
          }
          icon={<DollarSign className="w-4 h-4" />}
        />

        <MetricCard
          title="ROAS"
          value={summary.avg_roas ? summary.avg_roas.toFixed(1) : '—'}
          subtitle={
            summary.avg_roas
              ? summary.avg_roas >= 5
                ? '✅ Отличный результат'
                : summary.avg_roas >= 3
                ? '⚠️ Требует внимания'
                : '❌ Ниже целевого'
              : 'Нет конверсий'
          }
          icon={<TrendingUp className="w-4 h-4" />}
        />

        <MetricCard
          title="Конверсии сегодня"
          value={summary.total_conversions}
          subtitle={
            summary.total_leads > 0
              ? `CR: ${((summary.total_conversions / summary.total_leads) * 100).toFixed(1)}%`
              : 'Нет лидов'
          }
          icon={<Users className="w-4 h-4" />}
        />

        <MetricCard
          title="Кампании"
          value={`${summary.active_campaigns} / ${summary.total_campaigns}`}
          subtitle={`${summary.paused_campaigns} на паузе`}
          icon={<Target className="w-4 h-4" />}
        />
      </div>

      {/* Спидометр выручки и статус */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <RevenueSpeedometer
            current={summary.total_revenue_rub}
            target={100000} // TODO: из настроек target_monthly_revenue_rub
            label="Выручка за месяц"
          />
        </div>

        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Алерты и статусы */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {summary.avg_cac_rub && summary.avg_cac_rub <= 500 ? (
                  <CheckCircle className="w-4 h-4 text-dc-success-500" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-dc-warning-500" />
                )}
                Статус кампаний
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-dc-neutral-600">CAC</span>
                  <span className={`text-sm font-medium ${
                    summary.avg_cac_rub && summary.avg_cac_rub <= 500
                      ? 'text-dc-success-700'
                      : 'text-dc-warning-700'
                  }`}>
                    {summary.avg_cac_rub ? `${summary.avg_cac_rub.toFixed(0)}₽ / 500₽` : '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-dc-neutral-600">ROAS</span>
                  <span className={`text-sm font-medium ${
                    summary.avg_roas && summary.avg_roas >= 5
                      ? 'text-dc-success-700'
                      : 'text-dc-warning-700'
                  }`}>
                    {summary.avg_roas ? `${summary.avg_roas.toFixed(1)} / 5.0` : '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-dc-neutral-600">Активных кампаний</span>
                  <span className="text-sm font-medium text-dc-ink">
                    {summary.active_campaigns}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Использование бюджета</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-dc-neutral-600">Потрачено</span>
                    <span className="text-dc-ink font-medium">
                      {formatRub(summary.total_spent_rub)}
                    </span>
                  </div>
                  <div className="w-full bg-dc-warm-300 rounded-full h-2">
                    <div
                      className="bg-dc-accent-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(summary.budget_utilization, 100)}%` }}
                    />
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">
                    {summary.budget_utilization.toFixed(1)}% от бюджета
                  </div>
                </div>
                <div className="pt-2 border-t border-dc-warm-200">
                  <div className="text-sm text-dc-neutral-600">
                    Общий бюджет: {formatRub(summary.total_budget_rub)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Графики трендов */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>CAC и ROAS за 30 дней</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyMetrics && (
              <MetricChart
                data={dailyMetrics}
                metrics={['cac', 'roas']}
                height={250}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Конверсии и выручка</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyMetrics && (
              <MetricChart
                data={dailyMetrics}
                metrics={['conversions', 'revenue']}
                height={250}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Производительность каналов */}
      {channelData && (
        <ChannelPerformance data={channelData} />
      )}

      {/* Лучшие кампании */}
      <Card>
        <CardHeader>
          <CardTitle>Топ кампаний по ROAS</CardTitle>
        </CardHeader>
        <CardContent>
          {summary.top_performing_campaign ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-dc-warm-50 rounded-lg">
                <div>
                  <h4 className="font-semibold text-dc-ink">
                    🏆 {summary.top_performing_campaign.campaign_title}
                  </h4>
                  <p className="text-sm text-dc-neutral-600 mt-1">
                    Лучший ROAS за период
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-dc-success-700">
                    {summary.top_performing_campaign.roas.toFixed(1)}
                  </div>
                  <div className="text-sm text-dc-neutral-600">ROAS</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-dc-warm-200">
                <div className="text-center">
                  <div className="text-sm text-dc-neutral-600">Средний CAC</div>
                  <div className="text-xl font-bold text-dc-ink mt-1">
                    {summary.avg_cac_rub ? formatRub(summary.avg_cac_rub) : '—'}
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">
                    Цель: ≤ 500₽
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-dc-neutral-600">Средний ROAS</div>
                  <div className="text-xl font-bold text-dc-ink mt-1">
                    {summary.avg_roas ? summary.avg_roas.toFixed(1) : '—'}
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">
                    Цель: ≥ 5.0
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-dc-neutral-600">Conversion Rate</div>
                  <div className="text-xl font-bold text-dc-ink mt-1">
                    {summary.total_leads > 0
                      ? `${((summary.total_conversions / summary.total_leads) * 100).toFixed(1)}%`
                      : '—'}
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">
                    Цель: ≥ 10%
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-dc-neutral-500">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Нет данных о кампаниях</p>
              <p className="text-sm mt-1">Запустите первую кампанию для анализа</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

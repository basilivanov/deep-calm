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

  const { data: dailyMetrics } = useQuery<DailyMetricPoint[]>({
    queryKey: ['dashboard-daily-metrics'],
    queryFn: async () => {
      const response = await analyticsApi.dashboardDaily();
      return response.data;
    },
    refetchInterval: 300000,
  });

  const { data: channelData } = useQuery<ChannelPerformanceItem[]>({
    queryKey: ['dashboard-channel-performance'],
    queryFn: async () => {
      const response = await analyticsApi.channelPerformance();
      return response.data;
    },
    refetchInterval: 300000,
  });

  if (isLoading) {
    return (
      <div className="py-24 flex items-center justify-center">
        <div className="text-base font-medium text-dc-neutral">Загружаем свежие показатели…</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="py-24 flex items-center justify-center">
        <div className="text-base font-medium text-dc-neutral">Пока нет данных для отображения</div>
      </div>
    );
  }

  const formatRub = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="py-8 space-y-8">
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.24em] text-dc-neutral">Обзор</p>
        <h1 className="text-3xl font-semibold text-dc-primary">Маркетинговая панель</h1>
        <p className="text-sm text-dc-neutral">Ключевые метрики по воронкам и окупаемости рекламы</p>
      </div>

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          title="CAC текущий"
          value={summary.avg_cac_rub ? formatRub(summary.avg_cac_rub) : '—'}
          subtitle={
            summary.avg_cac_rub
              ? summary.avg_cac_rub <= 500
                ? '✅ В пределах цели'
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
                  ? '⚠️ Требуется внимание'
                  : '❌ Ниже плана'
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
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <RevenueSpeedometer
            current={summary.total_revenue_rub}
            target={100000}
            label="Выручка за месяц"
          />
        </div>

        <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-4">
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
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-dc-neutral-600">CAC</span>
                <span className={`font-medium ${summary.avg_cac_rub && summary.avg_cac_rub <= 500 ? 'text-dc-success-700' : 'text-dc-warning-700'}`}>
                  {summary.avg_cac_rub ? `${summary.avg_cac_rub.toFixed(0)}₽ / 500₽` : '—'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dc-neutral-600">ROAS</span>
                <span className={`font-medium ${summary.avg_roas && summary.avg_roas >= 5 ? 'text-dc-success-700' : 'text-dc-warning-700'}`}>
                  {summary.avg_roas ? `${summary.avg_roas.toFixed(1)} / 5.0` : '—'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dc-neutral-600">Активных кампаний</span>
                <span className="font-medium text-dc-ink">{summary.active_campaigns}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Использование бюджета</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-dc-neutral-600">Потрачено</span>
                  <span className="text-dc-ink font-medium">{formatRub(summary.total_spent_rub)}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-dc-warm-300/80">
                  <div
                    className="h-2 rounded-full bg-dc-accent"
                    style={{ width: `${Math.min(summary.budget_utilization, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-dc-neutral-500 mt-1">
                  {summary.budget_utilization.toFixed(1)}% от доступного бюджета
                </div>
              </div>
              <div className="text-sm text-dc-neutral-600">
                Общий бюджет: <span className="font-medium text-dc-ink">{formatRub(summary.total_budget_rub)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>CAC и ROAS за 30 дней</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyMetrics && (
              <MetricChart data={dailyMetrics} metrics={['cac', 'roas']} height={250} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Конверсии и выручка</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyMetrics && (
              <MetricChart data={dailyMetrics} metrics={['conversions', 'revenue']} height={250} />
            )}
          </CardContent>
        </Card>
      </section>

      {channelData && (
        <Card className="border border-dc-border shadow-sm">
          <CardHeader className="pb-0">
            <CardTitle className="text-dc-ink">Каналы</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <ChannelPerformance data={channelData} />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Топ кампаний по ROAS</CardTitle>
        </CardHeader>
        <CardContent>
          {summary.top_performing_campaign ? (
            <div className="space-y-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-4 bg-dc-warm-100 rounded-lg">
                <div>
                  <h4 className="font-semibold text-dc-ink">
                    🏆 {summary.top_performing_campaign.campaign_title}
                  </h4>
                  <p className="text-sm text-dc-neutral-600 mt-1">Лучший ROAS за период</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-dc-success-700">
                    {summary.top_performing_campaign.roas.toFixed(1)}
                  </div>
                  <div className="text-xs text-dc-neutral-600 uppercase tracking-wide">ROAS</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-dc-warm-200">
                <div className="text-center">
                  <div className="text-sm text-dc-neutral-600">Средний CAC</div>
                  <div className="text-xl font-bold text-dc-ink mt-1">
                    {summary.avg_cac_rub ? formatRub(summary.avg_cac_rub) : '—'}
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">Цель ≤ 500₽</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-dc-neutral-600">Средний ROAS</div>
                  <div className="text-xl font-bold text-dc-ink mt-1">
                    {summary.avg_roas ? summary.avg_roas.toFixed(1) : '—'}
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">Цель ≥ 5.0</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-dc-neutral-600">Conversion Rate</div>
                  <div className="text-xl font-bold text-dc-ink mt-1">
                    {summary.total_leads > 0
                      ? `${((summary.total_conversions / summary.total_leads) * 100).toFixed(1)}%`
                      : '—'}
                  </div>
                  <div className="text-xs text-dc-neutral-500 mt-1">Цель ≥ 10%</div>
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

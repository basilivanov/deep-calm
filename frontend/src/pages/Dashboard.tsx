import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, DollarSign, Target } from 'lucide-react';
import { analyticsApi, DashboardSummary } from '../api/client';
import { MetricCard } from '../components/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';

export function Dashboard() {
  const { data: summary, isLoading } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const response = await analyticsApi.dashboard();
      return response.data;
    },
    refetchInterval: 30000, // Обновление каждые 30 сек
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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Обзор всех кампаний и метрик
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Всего кампаний"
          value={summary.total_campaigns}
          subtitle={`${summary.active_campaigns} активных, ${summary.paused_campaigns} на паузе`}
          icon={<Target className="w-4 h-4" />}
        />

        <MetricCard
          title="Бюджет / Расход"
          value={formatRub(summary.total_spent_rub)}
          subtitle={`из ${formatRub(summary.total_budget_rub)} (${summary.budget_utilization.toFixed(1)}%)`}
          icon={<DollarSign className="w-4 h-4" />}
        />

        <MetricCard
          title="Лиды / Конверсии"
          value={`${summary.total_leads} / ${summary.total_conversions}`}
          subtitle={
            summary.total_leads > 0
              ? `CR: ${((summary.total_conversions / summary.total_leads) * 100).toFixed(1)}%`
              : 'Нет данных'
          }
          icon={<Users className="w-4 h-4" />}
        />

        <MetricCard
          title="Выручка"
          value={formatRub(summary.total_revenue_rub)}
          subtitle={
            summary.avg_roas
              ? `ROAS: ${summary.avg_roas.toFixed(2)}`
              : 'Нет конверсий'
          }
          icon={<TrendingUp className="w-4 h-4" />}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CAC Chart */}
        <Card>
          <CardHeader>
            <CardTitle>CAC по дням (последние 30 дней)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-gray-400">
              График CAC (в разработке)
            </div>
          </CardContent>
        </Card>

        {/* Conversion Rate Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Conversion Rate по дням</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-gray-400">
              График CR (в разработке)
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Средние показатели</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Средний CAC</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary.avg_cac_rub ? formatRub(summary.avg_cac_rub) : '—'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Средний ROAS</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary.avg_roas ? summary.avg_roas.toFixed(2) : '—'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Лучшая кампания</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white mt-1">
                {summary.top_performing_campaign
                  ? `${summary.top_performing_campaign.campaign_title} (ROAS: ${summary.top_performing_campaign.roas.toFixed(2)})`
                  : 'Нет данных'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

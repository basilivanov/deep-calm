import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  Users,
  DollarSign,
  Target,
  Activity
} from 'lucide-react';
import type { DashboardSummary, DailyMetricPoint, ChannelPerformanceItem } from '../api/client';
import { analyticsApi } from '../api/client';
import { MetricChart } from '../components/charts/MetricChart';
import { RevenueSpeedometer } from '../components/charts/RevenueSpeedometer';
import { ChannelPerformance } from '../components/charts/ChannelPerformance';

interface DashboardProps {
  onNavigate?: (page: 'dashboard' | 'campaigns' | 'integrations' | 'analyst') => void;
}

const EMPTY_SUMMARY: DashboardSummary = {
  total_campaigns: 0,
  active_campaigns: 0,
  paused_campaigns: 0,
  total_budget_rub: 0,
  total_spent_rub: 0,
  budget_utilization: 0,
  total_leads: 0,
  total_conversions: 0,
  total_revenue_rub: 0,
  avg_cac_rub: null,
  avg_roas: null,
  top_performing_campaign: null,
};

// Simple Metric Card Component
function MetricCard({ title, value, subtitle, icon: Icon, className = "" }: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: any;
  className?: string;
}) {
  return (
    <div className={`bg-white overflow-hidden shadow rounded-lg ${className}`}>
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="text-lg font-medium text-gray-900">
                {value}
              </dd>
            </dl>
          </div>
        </div>
        {subtitle && (
          <div className="mt-3">
            <div className="text-sm text-gray-500">
              {subtitle}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const queryClient = useQueryClient();

  const {
    data: summary,
    isLoading,
    isError,
  } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const response = await analyticsApi.dashboard();
      return response.data;
    },
    refetchInterval: 30000,
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

  const showEmpty = !isLoading && !isError && !summary;
  const isReady = Boolean(summary) && !isLoading && !isError;
  const effectiveSummary = summary ?? EMPTY_SUMMARY;

  const formatRub = (value: number) =>
    new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);

  const chartDailyData = dailyMetrics?.map((point) => ({
    ...point,
    cac: point.cac ?? undefined,
    roas: point.roas ?? undefined,
  }));

  const handleCreateCampaign = () => {
    if (onNavigate) {
      onNavigate('campaigns');
    }
  };

  const handleRefreshData = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-daily-metrics'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-channel-performance'] });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-gray-500">Загружаем данные...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Dashboard
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Обзор ключевых метрик и показателей эффективности
            </p>
          </div>
          <div className="mt-4 flex md:mt-0 md:ml-4">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              isReady ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {isReady ? 'Данные загружены' : 'Загрузка...'}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="CAC текущий"
          value={effectiveSummary.avg_cac_rub ? formatRub(effectiveSummary.avg_cac_rub) : '—'}
          subtitle={
            effectiveSummary.avg_cac_rub
              ? effectiveSummary.avg_cac_rub <= 500
                ? '✅ В пределах нормы'
                : '⚠️ Выше целевого'
              : 'Нет данных'
          }
          icon={DollarSign}
        />

        <MetricCard
          title="Активные кампании"
          value={`${effectiveSummary.active_campaigns}`}
          subtitle={`Всего: ${effectiveSummary.total_campaigns} | На паузе: ${effectiveSummary.paused_campaigns}`}
          icon={Target}
        />

        <MetricCard
          title="Конверсии"
          value={effectiveSummary.total_conversions.toLocaleString('ru-RU')}
          subtitle={
            effectiveSummary.total_leads > 0
              ? `CR: ${((effectiveSummary.total_conversions / effectiveSummary.total_leads) * 100).toFixed(1)}%`
              : 'Нет лидов'
          }
          icon={Users}
        />

        <MetricCard
          title="ROAS средний"
          value={effectiveSummary.avg_roas ? effectiveSummary.avg_roas.toFixed(1) : '—'}
          subtitle={effectiveSummary.avg_roas ? 'Рентабельность рекламы' : 'Нет данных'}
          icon={TrendingUp}
        />
      </div>

      {/* Revenue Section */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Выручка за месяц
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Цель: 100,000₽ | Текущая: {formatRub(effectiveSummary.total_revenue_rub)}
              </p>
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Прогресс к цели</span>
                  <span className="font-medium text-gray-900">
                    {Math.round((effectiveSummary.total_revenue_rub / 100000) * 100)}%
                  </span>
                </div>
                <div className="mt-2">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min((effectiveSummary.total_revenue_rub / 100000) * 100, 100)}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-center">
              <RevenueSpeedometer
                current={effectiveSummary.total_revenue_rub}
                target={100000}
                label="Выручка за месяц"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Daily Metrics Chart */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Динамика метрик
            </h3>
            {chartDailyData && chartDailyData.length > 0 ? (
              <MetricChart
                data={chartDailyData}
                metrics={['cac', 'roas', 'conversions', 'revenue', 'spend']}
              />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Недостаточно данных для графика</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Channel Performance */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Каналы привлечения
            </h3>
            {channelData && channelData.length > 0 ? (
              <ChannelPerformance data={channelData} />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Нет данных по каналам</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Быстрые действия
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Основные операции для управления кампаниями
              </p>
            </div>
            <div className="mt-4 sm:mt-0 sm:ml-4 flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleCreateCampaign}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Создать кампанию
              </button>
              <button
                onClick={handleRefreshData}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Обновить данные
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {showEmpty && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-12 sm:px-6 text-center">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <Target className="h-12 w-12" />
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Начните с первой кампании
            </h3>
            <p className="mt-1 text-sm text-gray-500 max-w-md mx-auto">
              Данных для дашборда пока нет. Запустите кампании, и статистика появится автоматически.
            </p>
            <div className="mt-6">
              <button
                onClick={handleCreateCampaign}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Создать кампанию
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
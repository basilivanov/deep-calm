import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, CheckCircle, AlertCircle, Key, RefreshCw, Shield, Link2, Activity, TrendingUp } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { MetricCardEnhanced } from '../components/ui/MetricCardEnhanced';
import { StatusPill } from '../components/ui/StatusPill';
import { Button } from '../components/ui/Button';
import { integrationsApi } from '../api/client';

interface Integration {
  id: string;
  name: string;
  type: 'vk' | 'direct' | 'avito' | 'yclients' | 'metrika';
  status: 'connected' | 'disconnected' | 'error' | 'pending';
  description: string;
  icon: string;
  color: string;
  lastSync?: string;
  errorMessage?: string;
  settings?: Record<string, string | number | boolean>;
}

export function Integrations() {
  const [showTokenForm, setShowTokenForm] = useState<string | null>(null);
  const [tokenInput, setTokenInput] = useState('');

  const queryClient = useQueryClient();

  // Получение списка интеграций с бэкенда
  const { data: integrations = [], isLoading } = useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      try {
        const response = await integrationsApi.list();
        return response.data;
      } catch (error) {
        console.error('Failed to fetch integrations:', error);
        // Fallback на mock данные если API недоступно
        return getMockIntegrations();
      }
    },
    refetchInterval: 30000,
  });

  const connectMutation = useMutation({
    mutationFn: async ({ type, token }: { type: string; token: string }) => {
      try {
        const response = await integrationsApi.connect(type, token);
        return response.data;
      } catch (error) {
        console.error('Failed to connect integration:', error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      setShowTokenForm(null);
      setTokenInput('');
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: async (integrationType: string) => {
      try {
        const response = await integrationsApi.disconnect(integrationType);
        return response.data;
      } catch (error) {
        console.error('Failed to disconnect integration:', error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  const syncMutation = useMutation({
    mutationFn: async (integrationType: string) => {
      try {
        const response = await integrationsApi.sync(integrationType);
        return response.data;
      } catch (error) {
        console.error('Failed to sync integration:', error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });


  const getStatusText = (status: Integration['status']) => {
    switch (status) {
      case 'connected': return 'Подключено';
      case 'error': return 'Ошибка';
      case 'pending': return 'Подключение...';
      default: return 'Не подключено';
    }
  };


  const formatLastSync = (date?: string) => {
    if (!date) return 'Никогда';
    const syncDate = new Date(date);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - syncDate.getTime()) / (1000 * 60 * 60));

    if (diffHours < 1) return 'Менее часа назад';
    if (diffHours < 24) return `${diffHours} ч. назад`;
    return syncDate.toLocaleDateString('ru-RU');
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[320px] items-center justify-center">
        <div className="text-sm font-medium text-dc-neutral">Загружаем интеграции…</div>
      </div>
    );
  }

  const connected = integrations.filter((i: Integration) => i.status === 'connected').length;
  const errored = integrations.filter((i: Integration) => i.status === 'error').length;
  const activeAds = integrations.filter((i: Integration) => ['vk', 'direct', 'avito'].includes(i.type) && i.status === 'connected').length;

  return (
    <div className="space-y-12">
      {/* Header Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-dc-primary">
              Интеграции
            </h1>
            <p className="text-dc-neutral-600 mt-2">
              Подключайте рекламные платформы, CRM и аналитические сервисы
            </p>
          </div>
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        <MetricCardEnhanced
          title="Всего интеграций"
          value={integrations.length.toString()}
          subtitle={`${connected} подключено`}
          icon={Settings}
          progress={{
            value: connected,
            max: Math.max(integrations.length, 1),
            label: 'Подключено'
          }}
          variant="glass"
        />

        <MetricCardEnhanced
          title="Подключено"
          value={connected.toString()}
          subtitle="Активные интеграции"
          icon={CheckCircle}
          status={{
            type: connected >= integrations.length - 1 ? 'success' : 'warning',
            text: connected >= integrations.length - 1 ? 'Все подключены' : 'Есть отключенные'
          }}
          variant="warm"
        />

        <MetricCardEnhanced
          title="Активные каналы"
          value={activeAds.toString()}
          subtitle="VK, Директ, Avito"
          icon={Activity}
          variant="gradient"
        />

        <MetricCardEnhanced
          title="Ошибок"
          value={errored.toString()}
          subtitle="Требуют внимания"
          icon={AlertCircle}
          status={{
            type: errored === 0 ? 'success' : 'error',
            text: errored === 0 ? 'Все работает' : 'Есть проблемы'
          }}
          variant="glass"
        />
      </div>

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {integrations.map((integration: Integration) => {
          const getStatusType = (status: Integration['status']) => {
            switch (status) {
              case 'connected': return 'success';
              case 'error': return 'error';
              case 'pending': return 'warning';
              default: return 'neutral';
            }
          };

          return (
            <GlassCard key={integration.id} variant="warm" className="hover:-translate-y-1 hover:scale-[1.01] transition-all duration-300">
              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div
                      className="flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg font-bold"
                      style={{ backgroundColor: integration.color }}
                    >
                      {integration.icon}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-dc-primary">{integration.name}</h3>
                      <p className="text-sm text-dc-neutral-600 mt-1">{integration.description}</p>
                    </div>
                  </div>
                  <StatusPill
                    status={getStatusType(integration.status)}
                    text={getStatusText(integration.status)}
                    variant="soft"
                  />
                </div>

                {/* Details */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <span className="text-xs uppercase tracking-[0.15em] text-dc-neutral-600 font-medium">
                      Последняя синхронизация
                    </span>
                    <p className="mt-1 text-sm font-semibold text-dc-primary">
                      {formatLastSync(integration.lastSync)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs uppercase tracking-[0.15em] text-dc-neutral-600 font-medium">
                      Тип подключения
                    </span>
                    <p className="mt-1 text-sm font-semibold text-dc-primary">
                      {integration.type.toUpperCase()}
                    </p>
                  </div>
                </div>

                {/* Error Message */}
                {integration.status === 'error' && integration.errorMessage && (
                  <div className="rounded-xl border border-dc-danger-300/60 bg-dc-danger-100/60 p-4">
                    <p className="text-sm text-dc-danger-700 flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      {integration.errorMessage}
                    </p>
                  </div>
                )}

                {/* Settings */}
                {integration.status === 'connected' && integration.settings && (
                  <div className="space-y-3">
                    <span className="text-xs uppercase tracking-[0.15em] text-dc-neutral-600 font-medium">
                      Настройки
                    </span>
                    <div className="grid gap-2">
                      {Object.entries(integration.settings).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between rounded-xl border border-dc-warm-400/60 bg-dc-warm-100/60 px-3 py-2">
                          <dt className="text-dc-neutral-700 capitalize font-medium">
                            {key.replace('_', ' ')}:
                          </dt>
                          <dd className="font-mono text-dc-primary text-sm">
                            {String(value)}
                          </dd>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-3 pt-2">
                  {integration.status === 'connected' ? (
                    <>
                      <button
                        onClick={() => syncMutation.mutate(integration.type)}
                        disabled={syncMutation.isPending}
                        className="px-4 py-2 bg-dc-accent-500 text-white rounded-xl font-medium hover:bg-dc-accent-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                      >
                        <RefreshCw className={`h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                        Синхронизировать
                      </button>
                      <button
                        onClick={() => disconnectMutation.mutate(integration.type)}
                        disabled={disconnectMutation.isPending}
                        className="px-4 py-2 border border-dc-danger-300/60 text-dc-danger-600 rounded-xl font-medium hover:bg-dc-danger-100/60 transition-colors disabled:opacity-50"
                      >
                        Отключить
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => {
                        if (integration.type === 'yclients') {
                          window.open('/api/v1/integrations/yclients/auth', '_blank');
                        } else {
                          setShowTokenForm(integration.type);
                        }
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-dc-accent-500 to-dc-primary-500 text-white rounded-xl font-medium hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
                    >
                      <Key className="h-4 w-4" />
                      Подключить
                    </button>
                  )}
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {/* Token Input Modal */}
      {showTokenForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="max-w-md w-full">
            <GlassCard variant="glass">
              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-dc-accent-100 text-dc-accent-600">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-dc-primary">
                      Подключение {integrations.find((i: Integration) => i.type === showTokenForm)?.name}
                    </h3>
                    <p className="text-sm text-dc-neutral-600">
                      Введите API токен для подключения
                    </p>
                  </div>
                </div>

                {/* Token Input */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-dc-primary">
                    API токен
                  </label>
                  <input
                    type="password"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    placeholder="Введите API токен..."
                    className="w-full p-3 border border-dc-warm-400/60 bg-dc-warm-50/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent text-dc-primary"
                  />
                  <p className="text-xs text-dc-neutral-600">
                    Токен будет зашифрован и сохранен безопасно
                  </p>
                </div>

                {/* Instructions */}
                <div className="p-4 bg-dc-warm-100/60 rounded-xl border border-dc-warm-400/60">
                  <p className="text-sm text-dc-primary font-semibold mb-3">
                    Как получить токен:
                  </p>
                  {showTokenForm === 'direct' && (
                    <ol className="text-sm text-dc-neutral-700 space-y-2 list-decimal list-inside">
                      <li>Войдите в <a href="https://direct.yandex.ru" target="_blank" className="text-dc-accent-600 hover:underline font-medium">Яндекс.Директ</a></li>
                      <li>Перейдите в настройки → API</li>
                      <li>Создайте новое приложение</li>
                      <li>Скопируйте токен доступа</li>
                    </ol>
                  )}
                  {showTokenForm === 'vk' && (
                    <ol className="text-sm text-dc-neutral-700 space-y-2 list-decimal list-inside">
                      <li>Войдите в <a href="https://vk.com/dev" target="_blank" className="text-dc-accent-600 hover:underline font-medium">VK Developers</a></li>
                      <li>Создайте standalone приложение</li>
                      <li>Получите токен с правами ads</li>
                    </ol>
                  )}
                  {showTokenForm === 'metrika' && (
                    <ol className="text-sm text-dc-neutral-700 space-y-2 list-decimal list-inside">
                      <li>Войдите в <a href="https://oauth.yandex.ru" target="_blank" className="text-dc-accent-600 hover:underline font-medium">Яндекс.OAuth</a></li>
                      <li>Зарегистрируйте приложение</li>
                      <li>Получите токен с доступом к Метрике</li>
                    </ol>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => connectMutation.mutate({ type: showTokenForm, token: tokenInput })}
                    disabled={!tokenInput.trim() || connectMutation.isPending}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-dc-accent-500 to-dc-primary-500 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:hover:scale-100"
                  >
                    {connectMutation.isPending ? 'Подключение...' : 'Подключить'}
                  </button>
                  <button
                    onClick={() => {
                      setShowTokenForm(null);
                      setTokenInput('');
                    }}
                    disabled={connectMutation.isPending}
                    className="px-4 py-3 border border-dc-warm-400/60 text-dc-neutral-600 rounded-xl font-semibold hover:bg-dc-warm-100/60 transition-colors disabled:opacity-50"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      )}
    </div>
  );
}

// Mock data для демонстрации
function getMockIntegrations(): Integration[] {
  return [
    {
      id: '1',
      name: 'Яндекс.Директ',
      type: 'direct',
      status: 'connected',
      description: 'Контекстная реклама в поиске Яндекса',
      icon: 'Я',
      color: '#FFCC00',
      lastSync: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      settings: {
        account_id: '700005756',
        client_id: 'massage_salon',
        daily_budget: '2000 ₽'
      }
    },
    {
      id: '2',
      name: 'VK Реклама',
      type: 'vk',
      status: 'disconnected',
      description: 'Таргетированная реклама ВКонтакте',
      icon: 'VK',
      color: '#4680C2'
    },
    {
      id: '3',
      name: 'Avito',
      type: 'avito',
      status: 'error',
      description: 'Продвижение объявлений на Авито',
      icon: 'A',
      color: '#00A956',
      errorMessage: 'Истек срок действия API ключа. Обновите токен.'
    },
    {
      id: '4',
      name: 'YCLIENTS',
      type: 'yclients',
      status: 'connected',
      description: 'Система записи и управления клиентами',
      icon: 'Y',
      color: '#FF6B35',
      lastSync: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 min ago
      settings: {
        company_id: '12345',
        location: 'Москва, Центр',
        services_count: '4'
      }
    },
    {
      id: '5',
      name: 'Яндекс.Метрика',
      type: 'metrika',
      status: 'connected',
      description: 'Аналитика и оффлайн-конверсии',
      icon: 'М',
      color: '#FF3333',
      lastSync: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
      settings: {
        counter_id: '98765432',
        goals_configured: '3',
        offline_conversions: 'enabled'
      }
    }
  ];
}

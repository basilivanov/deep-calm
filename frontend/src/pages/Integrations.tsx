import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, CheckCircle, AlertCircle, ExternalLink, Key, RefreshCw, Shield } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
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

  const getStatusIcon = (status: Integration['status']) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-5 h-5 text-dc-success-500" />;
      case 'error': return <AlertCircle className="w-5 h-5 text-dc-danger-500" />;
      case 'pending': return <RefreshCw className="w-5 h-5 text-dc-warning-500 animate-spin" />;
      default: return <AlertCircle className="w-5 h-5 text-dc-neutral-400" />;
    }
  };

  const getStatusText = (status: Integration['status']) => {
    switch (status) {
      case 'connected': return 'Подключено';
      case 'error': return 'Ошибка';
      case 'pending': return 'Подключение...';
      default: return 'Не подключено';
    }
  };

  const getStatusColor = (status: Integration['status']) => {
    switch (status) {
      case 'connected': return 'text-dc-success-700 bg-dc-success-100';
      case 'error': return 'text-dc-danger-700 bg-dc-danger-100';
      case 'pending': return 'text-dc-warning-700 bg-dc-warning-100';
      default: return 'text-dc-neutral-600 bg-dc-neutral-100';
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
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-dc-primary">
          Интеграции
        </h1>
        <p className="text-dc-primary/70 mt-1">
          Управление подключениями к рекламным платформам и сервисам
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Всего интеграций</p>
                <p className="text-2xl font-bold text-dc-ink">
                  {integrations.length}
                </p>
              </div>
              <Settings className="w-8 h-8 text-dc-primary-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Подключено</p>
                <p className="text-2xl font-bold text-dc-success-600">
                  {integrations.filter((i: Integration) => i.status === 'connected').length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-dc-success-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Ошибки</p>
                <p className="text-2xl font-bold text-dc-danger-600">
                  {integrations.filter((i: Integration) => i.status === 'error').length}
                </p>
              </div>
              <AlertCircle className="w-8 h-8 text-dc-danger-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Активных каналов</p>
                <p className="text-2xl font-bold text-dc-accent-600">
                  {integrations.filter((i: Integration) => ['vk', 'direct', 'avito'].includes(i.type) && i.status === 'connected').length}
                </p>
              </div>
              <ExternalLink className="w-8 h-8 text-dc-accent-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {integrations.map((integration: Integration) => (
          <Card key={integration.id} className="relative">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: integration.color }}
                  >
                    {integration.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-dc-ink">{integration.name}</h3>
                    <p className="text-sm text-dc-neutral-600">{integration.description}</p>
                  </div>
                </div>
                {getStatusIcon(integration.status)}
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-dc-neutral-600">Статус:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(integration.status)}`}>
                  {getStatusText(integration.status)}
                </span>
              </div>

              {/* Last Sync */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-dc-neutral-600">Последняя синхронизация:</span>
                <span className="text-sm text-dc-ink">{formatLastSync(integration.lastSync)}</span>
              </div>

              {/* Error Message */}
              {integration.status === 'error' && integration.errorMessage && (
                <div className="p-3 bg-dc-danger-50 border border-dc-danger-200 rounded-lg">
                  <p className="text-sm text-dc-danger-700">
                    <AlertCircle className="w-4 h-4 inline mr-2" />
                    {integration.errorMessage}
                  </p>
                </div>
              )}

              {/* Settings */}
              {integration.status === 'connected' && integration.settings && (
                <div className="space-y-2">
                  {Object.entries(integration.settings).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-dc-neutral-600 capitalize">{key.replace('_', ' ')}:</span>
                      <span className="text-dc-ink font-mono">{String(value)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                {integration.status === 'connected' ? (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => syncMutation.mutate(integration.type)}
                      disabled={syncMutation.isPending}
                      className="flex items-center gap-2"
                    >
                      <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                      Синхронизировать
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => disconnectMutation.mutate(integration.type)}
                      disabled={disconnectMutation.isPending}
                      className="text-dc-danger-600 hover:text-dc-danger-700"
                    >
                      Отключить
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      if (integration.type === 'yclients') {
                        // OAuth flow для YCLIENTS
                        window.open('/api/v1/integrations/yclients/auth', '_blank');
                      } else {
                        setShowTokenForm(integration.type);
                      }
                    }}
                    className="flex items-center gap-2"
                  >
                    <Key className="w-4 h-4" />
                    Подключить
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Token Input Modal */}
      {showTokenForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Подключение {integrations.find((i: Integration) => i.type === showTokenForm)?.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dc-ink mb-2">
                    API токен
                  </label>
                  <input
                    type="password"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    placeholder="Введите API токен..."
                    className="w-full p-3 border border-dc-warm-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent"
                  />
                  <p className="text-xs text-dc-neutral-600 mt-1">
                    Токен будет зашифрован и сохранен безопасно
                  </p>
                </div>

                {/* Instructions */}
                <div className="p-3 bg-dc-warm-50 rounded-lg">
                  <p className="text-sm text-dc-ink font-medium mb-2">
                    Как получить токен:
                  </p>
                  {showTokenForm === 'direct' && (
                    <ol className="text-sm text-dc-neutral-700 space-y-1 list-decimal list-inside">
                      <li>Войдите в <a href="https://direct.yandex.ru" target="_blank" className="text-dc-accent-600 hover:underline">Яндекс.Директ</a></li>
                      <li>Перейдите в настройки → API</li>
                      <li>Создайте новое приложение</li>
                      <li>Скопируйте токен доступа</li>
                    </ol>
                  )}
                  {showTokenForm === 'vk' && (
                    <ol className="text-sm text-dc-neutral-700 space-y-1 list-decimal list-inside">
                      <li>Войдите в <a href="https://vk.com/dev" target="_blank" className="text-dc-accent-600 hover:underline">VK Developers</a></li>
                      <li>Создайте standalone приложение</li>
                      <li>Получите токен с правами ads</li>
                    </ol>
                  )}
                  {showTokenForm === 'metrika' && (
                    <ol className="text-sm text-dc-neutral-700 space-y-1 list-decimal list-inside">
                      <li>Войдите в <a href="https://oauth.yandex.ru" target="_blank" className="text-dc-accent-600 hover:underline">Яндекс.OAuth</a></li>
                      <li>Зарегистрируйте приложение</li>
                      <li>Получите токен с доступом к Метрике</li>
                    </ol>
                  )}
                </div>

                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    onClick={() => connectMutation.mutate({ type: showTokenForm, token: tokenInput })}
                    disabled={!tokenInput.trim() || connectMutation.isPending}
                    className="flex-1"
                  >
                    {connectMutation.isPending ? 'Подключение...' : 'Подключить'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setShowTokenForm(null);
                      setTokenInput('');
                    }}
                    disabled={connectMutation.isPending}
                  >
                    Отмена
                  </Button>
                </div>
              </CardContent>
            </Card>
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
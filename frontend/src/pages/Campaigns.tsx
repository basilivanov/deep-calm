import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Play, Pause, Edit, Trash2, Eye, Target, DollarSign } from 'lucide-react';
import { campaignsApi, type Campaign } from '../api/client';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { CampaignForm } from '../components/CampaignForm';

export function Campaigns() {
  const [showForm, setShowForm] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);

  const queryClient = useQueryClient();

  const { data: campaignsData, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const response = await campaignsApi.list({ page: 1, page_size: 50 });
      return response.data;
    },
    refetchInterval: 30000,
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => campaignsApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => campaignsApi.pause(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => campaignsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const getStatusColor = (status: Campaign['status']) => {
    switch (status) {
      case 'active': return 'text-dc-success-700 bg-dc-success-100';
      case 'paused': return 'text-dc-warning-700 bg-dc-warning-100';
      case 'draft': return 'text-dc-neutral-600 bg-dc-neutral-100';
      case 'archived': return 'text-dc-neutral-500 bg-dc-neutral-50';
      default: return 'text-dc-neutral-600 bg-dc-neutral-100';
    }
  };

  const getStatusText = (status: Campaign['status']) => {
    switch (status) {
      case 'active': return 'Активна';
      case 'paused': return 'На паузе';
      case 'draft': return 'Черновик';
      case 'archived': return 'Архив';
      default: return status;
    }
  };

  const getChannelName = (channel: string) => {
    switch (channel) {
      case 'vk': return 'VK';
      case 'direct': return 'Яндекс.Директ';
      case 'avito': return 'Avito';
      default: return channel;
    }
  };

  const formatRub = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value);
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-dc-primary">
            Кампании
          </h1>
          <p className="text-dc-primary/70 mt-1">
            Управление рекламными кампаниями
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => {
            setEditingCampaign(null);
            setShowForm(true);
          }}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Создать кампанию
        </Button>
      </div>

      {/* Campaign Form Modal */}
      {showForm && (
        <CampaignForm
          campaign={editingCampaign}
          onSave={() => {
            setShowForm(false);
            setEditingCampaign(null);
            queryClient.invalidateQueries({ queryKey: ['campaigns'] });
          }}
          onCancel={() => {
            setShowForm(false);
            setEditingCampaign(null);
          }}
        />
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Всего кампаний</p>
                <p className="text-2xl font-bold text-dc-ink">
                  {campaignsData?.total || 0}
                </p>
              </div>
              <Target className="w-8 h-8 text-dc-primary-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Активных</p>
                <p className="text-2xl font-bold text-dc-success-600">
                  {campaignsData?.items.filter(c => c.status === 'active').length || 0}
                </p>
              </div>
              <Play className="w-8 h-8 text-dc-success-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">На паузе</p>
                <p className="text-2xl font-bold text-dc-warning-600">
                  {campaignsData?.items.filter(c => c.status === 'paused').length || 0}
                </p>
              </div>
              <Pause className="w-8 h-8 text-dc-warning-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dc-neutral-600">Общий бюджет</p>
                <p className="text-2xl font-bold text-dc-ink">
                  {formatRub(campaignsData?.items.reduce((sum, c) => sum + c.budget_rub, 0) || 0)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-dc-accent-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Campaigns List */}
      <Card>
        <CardHeader>
          <CardTitle>Список кампаний</CardTitle>
        </CardHeader>
        <CardContent>
          {campaignsData?.items.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-16 h-16 mx-auto text-dc-neutral-300 mb-4" />
              <h3 className="text-lg font-medium text-dc-ink mb-2">
                Нет кампаний
              </h3>
              <p className="text-dc-neutral-600 mb-6">
                Создайте первую кампанию для запуска рекламы
              </p>
              <Button
                variant="primary"
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Создать кампанию
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dc-warm-200">
                    <th className="text-left py-3 px-4 font-medium text-dc-ink">
                      Название
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-dc-ink">
                      SKU
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-dc-ink">
                      Каналы
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-dc-ink">
                      Бюджет
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-dc-ink">
                      Целевой CAC
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-dc-ink">
                      Статус
                    </th>
                    <th className="text-right py-3 px-4 font-medium text-dc-ink">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {campaignsData?.items.map((campaign) => (
                    <tr
                      key={campaign.id}
                      className="border-b border-dc-warm-100 hover:bg-dc-warm-50"
                    >
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium text-dc-ink">
                            {campaign.title}
                          </p>
                          <p className="text-sm text-dc-neutral-600">
                            {new Date(campaign.created_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-dc-accent-100 text-dc-accent-800">
                          {campaign.sku}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {campaign.channels.map((channel) => (
                            <span
                              key={channel}
                              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-dc-primary-100 text-dc-primary-800"
                            >
                              {getChannelName(channel)}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-dc-ink">
                        {formatRub(campaign.budget_rub)}
                      </td>
                      <td className="py-3 px-4 text-dc-ink">
                        {formatRub(campaign.target_cac_rub)}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(campaign.status)}`}>
                          {getStatusText(campaign.status)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              // TODO: navigate to campaign details
                            }}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>

                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setEditingCampaign(campaign);
                              setShowForm(true);
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>

                          {campaign.status === 'active' ? (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => pauseMutation.mutate(campaign.id)}
                              disabled={pauseMutation.isPending}
                            >
                              <Pause className="w-4 h-4" />
                            </Button>
                          ) : campaign.status === 'paused' || campaign.status === 'draft' ? (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => activateMutation.mutate(campaign.id)}
                              disabled={activateMutation.isPending}
                            >
                              <Play className="w-4 h-4" />
                            </Button>
                          ) : null}

                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              if (confirm('Удалить кампанию? Это действие нельзя отменить.')) {
                                deleteMutation.mutate(campaign.id);
                              }
                            }}
                            disabled={deleteMutation.isPending}
                            className="text-dc-danger-600 hover:text-dc-danger-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
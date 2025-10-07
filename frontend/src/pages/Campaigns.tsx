import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Play, Pause, Edit, Trash2, Eye, Target, DollarSign, Activity } from 'lucide-react';
import { campaignsApi, type Campaign } from '../api/client';
import { GlassCard } from '../components/ui/GlassCard';
import { MetricCardEnhanced } from '../components/ui/MetricCardEnhanced';
import { StatusPill } from '../components/ui/StatusPill';
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

  const campaigns = campaignsData?.items ?? [];
  const totalCampaigns = campaignsData?.total ?? campaigns.length;
  const activeCampaigns = campaigns.filter((c) => c.status === 'active').length;
  const pausedCampaigns = campaigns.filter((c) => c.status === 'paused').length;
  const totalBudget = campaigns.reduce((sum, c) => sum + c.budget_rub, 0);
  const uniqueChannels = Array.from(new Set(campaigns.flatMap((campaign) => campaign.channels)));

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
      <div className="py-24 flex items-center justify-center">
        <div className="text-base font-medium text-dc-neutral">Загружаем кампании…</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 lg:space-y-12">
      {/* Header Section */}
      <div className="space-y-4 lg:space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-dc-primary">
              Кампании
            </h1>
            <p className="text-dc-neutral-600 mt-2">
              Планируйте бюджеты, управляйте статусами и синхронизациями с каналами в одном месте
            </p>
          </div>
          <div className="flex-shrink-0">
            <button
              onClick={() => {
                setEditingCampaign(null);
                setShowForm(true);
              }}
              className="px-4 py-2 lg:px-6 lg:py-3 bg-gradient-to-r from-dc-accent-500 to-dc-primary-500 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg flex items-center gap-2 text-sm lg:text-base w-full sm:w-auto justify-center"
            >
              <Plus className="w-4 h-4" />
              Создать кампанию
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 lg:gap-6">
        <MetricCardEnhanced
          title="Всего кампаний"
          value={totalCampaigns.toString()}
          subtitle={`Активных: ${activeCampaigns}`}
          icon={Target}
          progress={{
            value: activeCampaigns,
            max: Math.max(totalCampaigns, 1),
            label: 'Активность'
          }}
          variant="glass"
        />

        <MetricCardEnhanced
          title="Общий бюджет"
          value={formatRub(totalBudget)}
          subtitle={campaigns.length ? `Средний: ${formatRub(totalBudget / campaigns.length)}` : 'Нет кампаний'}
          icon={DollarSign}
          variant="warm"
        />

        <MetricCardEnhanced
          title="Каналы"
          value={uniqueChannels.length.toString()}
          subtitle="VK, Яндекс.Директ, Avito"
          icon={Activity}
          status={{
            type: uniqueChannels.length >= 2 ? 'success' : 'warning',
            text: uniqueChannels.length >= 2 ? 'Многоканальность' : 'Один канал'
          }}
          variant="gradient"
        />

        <MetricCardEnhanced
          title="На паузе"
          value={pausedCampaigns.toString()}
          subtitle="Проверьте настройки креативов"
          icon={Pause}
          status={{
            type: pausedCampaigns === 0 ? 'success' : 'warning',
            text: pausedCampaigns === 0 ? 'Все активны' : 'Требует внимания'
          }}
          variant="glass"
        />
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

      <GlassCard variant="glass" className="overflow-hidden">
        <div className="p-4 lg:p-6 border-b border-dc-warm-300/40">
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.2em] text-dc-neutral-500 font-medium">
              Актуальные кампании
            </p>
            <h2 className="text-2xl font-bold text-dc-primary">
              Список кампаний
            </h2>
          </div>
        </div>

        <div className="p-4 lg:p-6">
          {campaigns.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-4 lg:gap-6 py-8 lg:py-12 text-center">
              <div className="w-16 h-16 bg-dc-warm-200 rounded-full flex items-center justify-center">
                <Target className="w-8 h-8 text-dc-accent-600" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-semibold text-dc-primary">
                  Нет кампаний
                </h3>
                <p className="text-dc-neutral-600 max-w-sm">
                  Создайте первую кампанию для запуска рекламы
                </p>
              </div>
              <button
                onClick={() => setShowForm(true)}
                className="px-6 py-3 bg-gradient-to-r from-dc-accent-500 to-dc-primary-500 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Создать кампанию
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {campaigns.map((campaign) => {
                const createdAt = new Date(campaign.created_at).toLocaleDateString('ru-RU');
                const getStatusType = (status: Campaign['status']) => {
                  switch (status) {
                    case 'active': return 'success';
                    case 'paused': return 'warning';
                    case 'draft': return 'neutral';
                    case 'archived': return 'inactive';
                    default: return 'neutral';
                  }
                };

                return (
                  <GlassCard
                    key={campaign.id}
                    variant="warm"
                    className="hover:-translate-y-1 hover:scale-[1.01] transition-all duration-300"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                      {/* Campaign Info */}
                      <div className="space-y-4 flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-lg font-semibold text-dc-primary">
                              {campaign.title}
                            </h3>
                            <p className="text-sm text-dc-neutral-600 mt-1">
                              Создана {createdAt}
                            </p>
                          </div>
                          <StatusPill
                            status={getStatusType(campaign.status)}
                            text={getStatusText(campaign.status)}
                            variant="soft"
                          />
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <span className="inline-flex items-center rounded-full border border-dc-accent-300/60 bg-dc-accent-100/60 px-3 py-1 text-xs font-medium text-dc-accent-700">
                            SKU: {campaign.sku}
                          </span>
                          {campaign.channels.map((channel) => (
                            <span
                              key={channel}
                              className="inline-flex items-center rounded-full border border-dc-warm-400/60 bg-dc-warm-100/60 px-3 py-1 text-xs text-dc-neutral-700"
                            >
                              {getChannelName(channel)}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Campaign Stats */}
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 text-center lg:text-right min-w-[300px]">
                        <div>
                          <p className="text-xs uppercase tracking-[0.15em] text-dc-neutral-600 font-medium">
                            Бюджет
                          </p>
                          <p className="text-lg font-semibold text-dc-primary mt-1">
                            {formatRub(campaign.budget_rub)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-[0.15em] text-dc-neutral-600 font-medium">
                            Целевой CAC
                          </p>
                          <p className="text-lg font-semibold text-dc-primary mt-1">
                            {formatRub(campaign.target_cac_rub)}
                          </p>
                        </div>
                        <div className="col-span-2 lg:col-span-1 flex justify-center lg:justify-end gap-2">
                          <button
                            onClick={() => {
                              // TODO: navigate to campaign details
                            }}
                            className="p-2 rounded-xl border border-dc-warm-400/60 text-dc-neutral-600 hover:bg-dc-warm-100/80 transition-colors"
                            title="Просмотр"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              setEditingCampaign(campaign);
                              setShowForm(true);
                            }}
                            className="p-2 rounded-xl border border-dc-warm-400/60 text-dc-neutral-600 hover:bg-dc-warm-100/80 transition-colors"
                            title="Редактировать"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          {campaign.status === 'active' ? (
                            <button
                              onClick={() => pauseMutation.mutate(campaign.id)}
                              disabled={pauseMutation.isPending}
                              className="p-2 rounded-xl border border-dc-warning-300/60 text-dc-warning-600 hover:bg-dc-warning-100/80 transition-colors disabled:opacity-50"
                              title="Поставить на паузу"
                            >
                              <Pause className="h-4 w-4" />
                            </button>
                          ) : campaign.status === 'paused' || campaign.status === 'draft' ? (
                            <button
                              onClick={() => activateMutation.mutate(campaign.id)}
                              disabled={activateMutation.isPending}
                              className="p-2 rounded-xl border border-dc-success-300/60 text-dc-success-600 hover:bg-dc-success-100/80 transition-colors disabled:opacity-50"
                              title="Запустить"
                            >
                              <Play className="h-4 w-4" />
                            </button>
                          ) : null}
                          <button
                            onClick={() => {
                              if (confirm('Удалить кампанию? Это действие нельзя отменить.')) {
                                deleteMutation.mutate(campaign.id);
                              }
                            }}
                            disabled={deleteMutation.isPending}
                            className="p-2 rounded-xl border border-dc-danger-300/60 text-dc-danger-600 hover:bg-dc-danger-100/80 transition-colors disabled:opacity-50"
                            title="Удалить"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}

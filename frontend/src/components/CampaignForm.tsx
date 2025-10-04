import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { X, Sparkles, Target } from 'lucide-react';
import { campaignsApi, type Campaign, type CreateCampaignRequest } from '../api/client';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Button } from './ui/Button';

interface CampaignFormProps {
  campaign?: Campaign | null;
  onSave: () => void;
  onCancel: () => void;
}

const SKU_OPTIONS = [
  { value: 'RELAX-60', label: 'Релаксационный массаж (60 мин)', price: 3500 },
  { value: 'DEEP-90', label: 'Глубокий массаж (90 мин)', price: 5000 },
  { value: 'ANTI-STRESS-45', label: 'Антистресс (45 мин)', price: 2800 },
  { value: 'THERAPY-120', label: 'Лечебный массаж (120 мин)', price: 7000 },
];

const CHANNEL_OPTIONS = [
  { value: 'vk', label: 'VK Реклама', color: '#4680C2', description: 'ВКонтакте таргетированная реклама' },
  { value: 'direct', label: 'Яндекс.Директ', color: '#FFCC00', description: 'Контекстная реклама в поиске' },
  { value: 'avito', label: 'Avito', color: '#00A956', description: 'Объявления на Авито' },
];

export function CampaignForm({ campaign, onSave, onCancel }: CampaignFormProps) {
  const [formData, setFormData] = useState<CreateCampaignRequest>({
    title: '',
    sku: 'RELAX-60',
    budget_rub: 15000,
    target_cac_rub: 500,
    target_roas: 5.0,
    channels: [],
    ab_test_enabled: true,
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    if (campaign) {
      setFormData({
        title: campaign.title,
        sku: campaign.sku,
        budget_rub: campaign.budget_rub,
        target_cac_rub: campaign.target_cac_rub,
        target_roas: campaign.target_roas,
        channels: campaign.channels,
        ab_test_enabled: campaign.ab_test_enabled,
      });
    }
  }, [campaign]);

  const createMutation = useMutation({
    mutationFn: (data: CreateCampaignRequest) => campaignsApi.create(data),
    onSuccess: () => {
      onSave();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<CreateCampaignRequest>) =>
      campaignsApi.update(campaign!.id, data),
    onSuccess: () => {
      onSave();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (campaign) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleChannelToggle = (channelValue: string) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channelValue)
        ? prev.channels.filter(ch => ch !== channelValue)
        : [...prev.channels, channelValue]
    }));
  };

  const selectedSku = SKU_OPTIONS.find(sku => sku.value === formData.sku);
  const estimatedConversions = Math.round(formData.budget_rub / formData.target_cac_rub);
  const estimatedRevenue = estimatedConversions * (selectedSku?.price || 0);
  const estimatedRoas = estimatedRevenue / formData.budget_rub;

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5" />
              {campaign ? 'Редактировать кампанию' : 'Создать кампанию'}
            </CardTitle>
            <Button variant="secondary" size="sm" onClick={onCancel}>
              <X className="w-4 h-4" />
            </Button>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Основные настройки */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dc-ink mb-2">
                    Название кампании
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Например: Релакс массаж - октябрь 2024"
                    className="w-full p-3 border border-dc-warm-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-dc-ink mb-2">
                    Услуга (SKU)
                  </label>
                  <select
                    value={formData.sku}
                    onChange={(e) => setFormData(prev => ({ ...prev, sku: e.target.value }))}
                    className="w-full p-3 border border-dc-warm-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent"
                  >
                    {SKU_OPTIONS.map((sku) => (
                      <option key={sku.value} value={sku.value}>
                        {sku.label} — {sku.price.toLocaleString('ru-RU')}₽
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-dc-ink mb-2">
                      Бюджет кампании
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        value={formData.budget_rub}
                        onChange={(e) => setFormData(prev => ({ ...prev, budget_rub: Number(e.target.value) }))}
                        min="1000"
                        step="1000"
                        className="w-full p-3 border border-dc-warm-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent pr-12"
                        required
                      />
                      <span className="absolute right-3 top-3 text-dc-neutral-500">₽</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dc-ink mb-2">
                      Целевой CAC
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        value={formData.target_cac_rub}
                        onChange={(e) => setFormData(prev => ({ ...prev, target_cac_rub: Number(e.target.value) }))}
                        min="100"
                        step="50"
                        className="w-full p-3 border border-dc-warm-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent pr-12"
                        required
                      />
                      <span className="absolute right-3 top-3 text-dc-neutral-500">₽</span>
                    </div>
                    <p className="text-xs text-dc-neutral-600 mt-1">
                      Рекомендуемый: ≤ 500₽
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dc-ink mb-3">
                    Каналы размещения
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {CHANNEL_OPTIONS.map((channel) => (
                      <div
                        key={channel.value}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          formData.channels.includes(channel.value)
                            ? 'border-dc-accent-500 bg-dc-accent-50'
                            : 'border-dc-warm-300 hover:border-dc-accent-300'
                        }`}
                        onClick={() => handleChannelToggle(channel.value)}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: channel.color }}
                          />
                          <div className="flex-1">
                            <p className="font-medium text-dc-ink">{channel.label}</p>
                            <p className="text-xs text-dc-neutral-600">{channel.description}</p>
                          </div>
                          {formData.channels.includes(channel.value) && (
                            <div className="w-5 h-5 bg-dc-accent-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-xs">✓</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {formData.channels.length === 0 && (
                    <p className="text-sm text-dc-danger-600 mt-2">
                      Выберите хотя бы один канал размещения
                    </p>
                  )}
                </div>
              </div>

              {/* Дополнительные настройки */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-dc-accent-600 hover:text-dc-accent-700 font-medium"
                >
                  <Sparkles className="w-4 h-4" />
                  Дополнительные настройки
                  <span className={`transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </button>

                {showAdvanced && (
                  <div className="mt-4 space-y-4 p-4 bg-dc-warm-50 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-dc-ink mb-2">
                        Целевой ROAS
                      </label>
                      <input
                        type="number"
                        value={formData.target_roas}
                        onChange={(e) => setFormData(prev => ({ ...prev, target_roas: Number(e.target.value) }))}
                        min="1"
                        step="0.1"
                        className="w-full p-3 border border-dc-warm-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent"
                      />
                      <p className="text-xs text-dc-neutral-600 mt-1">
                        Рекомендуемый: ≥ 5.0 (выручка должна в 5 раз превышать расходы)
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        id="ab-test"
                        checked={formData.ab_test_enabled}
                        onChange={(e) => setFormData(prev => ({ ...prev, ab_test_enabled: e.target.checked }))}
                        className="w-4 h-4 text-dc-accent-600 border-dc-warm-300 rounded focus:ring-dc-accent-500"
                      />
                      <label htmlFor="ab-test" className="text-sm text-dc-ink">
                        Включить A/B тестирование креативов
                      </label>
                    </div>
                  </div>
                )}
              </div>

              {/* Прогноз */}
              {formData.budget_rub > 0 && formData.target_cac_rub > 0 && (
                <div className="p-4 bg-dc-primary-50 rounded-lg">
                  <h4 className="font-medium text-dc-ink mb-3">📊 Прогноз результатов</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-dc-neutral-600">Конверсии</p>
                      <p className="font-bold text-dc-ink">~{estimatedConversions}</p>
                    </div>
                    <div>
                      <p className="text-dc-neutral-600">Выручка</p>
                      <p className="font-bold text-dc-ink">
                        {estimatedRevenue.toLocaleString('ru-RU')}₽
                      </p>
                    </div>
                    <div>
                      <p className="text-dc-neutral-600">ROAS</p>
                      <p className={`font-bold ${
                        estimatedRoas >= 5 ? 'text-dc-success-600' :
                        estimatedRoas >= 3 ? 'text-dc-warning-600' :
                        'text-dc-danger-600'
                      }`}>
                        {estimatedRoas.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-dc-neutral-600">Прибыль</p>
                      <p className={`font-bold ${
                        estimatedRevenue > formData.budget_rub ? 'text-dc-success-600' : 'text-dc-danger-600'
                      }`}>
                        {(estimatedRevenue - formData.budget_rub).toLocaleString('ru-RU', { signDisplay: 'always' })}₽
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Действия */}
              <div className="flex gap-3 pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isLoading || formData.channels.length === 0}
                  className="flex-1"
                >
                  {isLoading ? 'Сохранение...' : campaign ? 'Сохранить изменения' : 'Создать кампанию'}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onCancel}
                  disabled={isLoading}
                >
                  Отмена
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
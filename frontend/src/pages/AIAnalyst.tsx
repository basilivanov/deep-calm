import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bot, Brain, TrendingUp, Target, Lightbulb, Activity, Zap } from 'lucide-react';
import { AIChat } from '../components/AIChat';
import { GlassCard } from '../components/ui/GlassCard';
import { MetricCardEnhanced } from '../components/ui/MetricCardEnhanced';
import { StatusPill } from '../components/ui/StatusPill';

interface Campaign {
  id: number;
  title: string;
  status: string;
  sku: string;
}

interface AnalysisResult {
  campaign_id: number;
  analysis: string;
  metrics: {
    roas: number;
    cac: number;
    conversion_rate: number;
    total_leads: number;
    total_conversions: number;
  };
  recommendations: string[];
  generated_at: string;
}

export const AIAnalyst: React.FC = () => {
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const { data: campaigns } = useQuery<{ items: Campaign[] }>({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const response = await fetch('/api/v1/campaigns');
      if (!response.ok) throw new Error('Failed to fetch campaigns');
      return response.json();
    },
  });

  const { data: healthStatus } = useQuery({
    queryKey: ['analyst-health'],
    queryFn: async () => {
      const response = await fetch('/api/v1/analyst/health');
      if (!response.ok) throw new Error('Failed to check analyst health');
      return response.json();
    },
  });

  const analyzeCampaign = async (campaignId: number) => {
    setIsAnalyzing(true);
    try {
      const response = await fetch(`/api/v1/analyst/analyze/${campaignId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Ошибка анализа');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (error) {
      console.error('Analysis error:', error);
      alert('Ошибка анализа кампании. Проверьте настройки OpenAI API.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-12">
      {/* Header Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-dc-accent-100 to-dc-primary-100 border border-dc-accent-200">
              <Bot className="w-8 h-8 text-dc-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-dc-primary">
                AI Analyst
              </h1>
              <p className="text-dc-neutral-600 mt-2">
                Анализируйте кампании и получайте автоматические инсайты
              </p>
            </div>
          </div>
          {healthStatus && (
            <StatusPill
              status={
                healthStatus.status === 'ok' ? 'success' :
                healthStatus.status === 'warning' ? 'warning' : 'error'
              }
              text={healthStatus.message || healthStatus.status}
              variant="soft"
            />
          )}
        </div>
      </div>

      {/* Service Status */}
      {healthStatus && (
        <MetricCardEnhanced
          title="AI Сервис"
          value={healthStatus.status === 'ok' ? 'Активен' : 'Проблема'}
          subtitle={healthStatus.message || 'Статус системы'}
          icon={Brain}
          status={{
            type: healthStatus.status === 'ok' ? 'success' :
                  healthStatus.status === 'warning' ? 'warning' : 'error',
            text: healthStatus.status === 'ok' ? 'Готов к работе' : 'Требует внимания'
          }}
          variant="gradient"
        >
          {healthStatus.settings && (
            <div className="text-xs text-dc-neutral-600 space-y-1">
              <div>Модель: <span className="font-mono">{healthStatus.settings.model}</span></div>
              <div>Temperature: <span className="font-mono">{healthStatus.settings.temperature}</span></div>
              <div>Max tokens: <span className="font-mono">{healthStatus.settings.max_tokens}</span></div>
            </div>
          )}
        </MetricCardEnhanced>
      )}

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Campaign Analysis Panel */}
        <GlassCard variant="glass" className="h-full">
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-dc-accent-100 text-dc-accent-600">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-dc-primary">Анализ кампаний</h2>
                <p className="text-sm text-dc-neutral-600 mt-1">
                  Выберите кампанию для получения подробного анализа
                </p>
              </div>
            </div>

            {/* Campaign Selection */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-dc-primary">
                Выберите кампанию:
              </label>
              <select
                value={selectedCampaign?.id || ''}
                onChange={(e) => {
                  const campaign = campaigns?.items.find((c) => c.id === parseInt(e.target.value, 10));
                  setSelectedCampaign(campaign || null);
                  setAnalysisResult(null);
                }}
                className="w-full p-3 border border-dc-warm-400/60 bg-dc-warm-50/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-dc-accent-500 focus:border-transparent text-dc-primary"
              >
                <option value="">-- Выберите кампанию --</option>
                {campaigns?.items.map((campaign) => (
                  <option key={campaign.id} value={campaign.id}>
                    {campaign.title} ({campaign.sku}) — {campaign.status}
                  </option>
                ))}
              </select>
            </div>

            {/* Analyze Button */}
            {selectedCampaign && (
              <button
                onClick={() => analyzeCampaign(selectedCampaign.id)}
                disabled={isAnalyzing}
                className="w-full px-4 py-3 bg-gradient-to-r from-dc-accent-500 to-dc-primary-500 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    Анализирую…
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Анализировать кампанию
                  </>
                )}
              </button>
            )}

            {/* Analysis Results */}
            {analysisResult && (
              <div className="space-y-6">
                {/* Metrics */}
                <div className="p-4 bg-dc-warm-100/60 rounded-xl border border-dc-warm-400/60">
                  <h3 className="text-sm font-semibold text-dc-primary mb-3 flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Метрики
                  </h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-dc-neutral-600">ROAS:</span>
                      <span className="font-semibold text-dc-primary">{analysisResult.metrics.roas}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dc-neutral-600">CAC:</span>
                      <span className="font-semibold text-dc-primary">{analysisResult.metrics.cac} ₽</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dc-neutral-600">CR:</span>
                      <span className="font-semibold text-dc-primary">{analysisResult.metrics.conversion_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dc-neutral-600">Лиды:</span>
                      <span className="font-semibold text-dc-primary">{analysisResult.metrics.total_leads}</span>
                    </div>
                  </div>
                </div>

                {/* AI Analysis */}
                <div className="p-4 bg-dc-warm-100/60 rounded-xl border border-dc-warm-400/60">
                  <h3 className="text-sm font-semibold text-dc-primary mb-3 flex items-center gap-2">
                    <Brain className="w-4 h-4" />
                    Анализ AI
                  </h3>
                  <div className="whitespace-pre-wrap text-sm text-dc-neutral-700">
                    {analysisResult.analysis}
                  </div>
                </div>

                {/* Recommendations */}
                {analysisResult.recommendations.length > 0 && (
                  <div className="p-4 bg-gradient-to-br from-dc-accent-100/60 to-dc-primary-100/60 rounded-xl border border-dc-accent-300/60">
                    <h3 className="text-sm font-semibold text-dc-primary mb-3 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4" />
                      Рекомендации
                    </h3>
                    <ul className="space-y-2 text-sm">
                      {analysisResult.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-dc-accent-600 mt-1">•</span>
                          <span className="text-dc-neutral-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </GlassCard>

        {/* AI Chat Panel */}
        <GlassCard variant="warm" className="h-full">
          <AIChat
            campaignId={selectedCampaign?.id}
            campaignTitle={selectedCampaign?.title}
          />
        </GlassCard>
      </div>

      {/* Examples Section */}
      <GlassCard variant="gradient">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-dc-accent-100 text-dc-accent-600">
              <Lightbulb className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-dc-primary">Примеры запросов</h3>
              <p className="text-sm text-dc-neutral-600 mt-1">
                Попробуйте эти запросы для получения экспертных рекомендаций
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="p-4 bg-dc-warm-100/60 rounded-xl border border-dc-warm-400/60 hover:bg-dc-warm-200/60 transition-colors cursor-pointer">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-dc-accent-600" />
                <p className="font-semibold text-dc-primary">Оптимизация</p>
              </div>
              <p className="text-sm text-dc-neutral-700">
                «Как снизить CAC для кампаний массажа?»
              </p>
            </div>

            <div className="p-4 bg-dc-warm-100/60 rounded-xl border border-dc-warm-400/60 hover:bg-dc-warm-200/60 transition-colors cursor-pointer">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-dc-accent-600" />
                <p className="font-semibold text-dc-primary">Стратегия</p>
              </div>
              <p className="text-sm text-dc-neutral-700">
                «Какие каналы лучше работают для салонов красоты?»
              </p>
            </div>

            <div className="p-4 bg-dc-warm-100/60 rounded-xl border border-dc-warm-400/60 hover:bg-dc-warm-200/60 transition-colors cursor-pointer">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-dc-accent-600" />
                <p className="font-semibold text-dc-primary">Сезонность</p>
              </div>
              <p className="text-sm text-dc-neutral-700">
                «Как подготовиться к новогоднему пику спроса?»
              </p>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AIChat } from '../components/AIChat';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

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

  // Получаем список кампаний
  const { data: campaigns } = useQuery<{ items: Campaign[] }>({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const response = await fetch('/api/v1/campaigns');
      if (!response.ok) throw new Error('Failed to fetch campaigns');
      return response.json();
    }
  });

  // Проверяем статус AI Analyst
  const { data: healthStatus } = useQuery({
    queryKey: ['analyst-health'],
    queryFn: async () => {
      const response = await fetch('/api/v1/analyst/health');
      if (!response.ok) throw new Error('Failed to check analyst health');
      return response.json();
    }
  });

  const analyzeCampaign = async (campaignId: number) => {
    setIsAnalyzing(true);
    try {
      const response = await fetch(`/api/v1/analyst/analyze/${campaignId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
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
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-dc-primary mb-2">
          🤖 AI Analyst
        </h1>
        <p className="text-dc-text">
          Анализ кампаний и консультации по performance маркетингу
        </p>
      </div>

      {/* Health Status */}
      {healthStatus && (
        <Card className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-dc-primary">Статус AI Сервиса</h3>
              <p className={`text-sm ${
                healthStatus.status === 'ok' ? 'text-green-600' :
                healthStatus.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {healthStatus.message || healthStatus.status}
              </p>
            </div>
            <div className={`w-3 h-3 rounded-full ${
              healthStatus.status === 'ok' ? 'bg-green-500' :
              healthStatus.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
          </div>
          {healthStatus.settings && (
            <div className="mt-2 text-xs text-gray-600">
              Модель: {healthStatus.settings.model} |
              Temperature: {healthStatus.settings.temperature} |
              Max tokens: {healthStatus.settings.max_tokens}
            </div>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Campaign Analysis */}
        <div className="space-y-4">
          <Card>
            <h2 className="text-xl font-semibold text-dc-primary mb-4">
              📊 Анализ кампаний
            </h2>

            {/* Campaign Selector */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-dc-text mb-2">
                Выберите кампанию:
              </label>
              <select
                value={selectedCampaign?.id || ''}
                onChange={(e) => {
                  const campaign = campaigns?.items.find(c => c.id === parseInt(e.target.value));
                  setSelectedCampaign(campaign || null);
                  setAnalysisResult(null);
                }}
                className="w-full p-2 border border-dc-primary/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-dc-accent"
              >
                <option value="">-- Выберите кампанию --</option>
                {campaigns?.items.map((campaign) => (
                  <option key={campaign.id} value={campaign.id}>
                    {campaign.title} ({campaign.sku}) - {campaign.status}
                  </option>
                ))}
              </select>
            </div>

            {/* Analyze Button */}
            {selectedCampaign && (
              <Button
                onClick={() => analyzeCampaign(selectedCampaign.id)}
                disabled={isAnalyzing}
                className="w-full mb-4"
              >
                {isAnalyzing ? '🔄 Анализирую...' : '🚀 Анализировать кампанию'}
              </Button>
            )}

            {/* Analysis Results */}
            {analysisResult && (
              <div className="space-y-4">
                <div className="bg-dc-bg p-4 rounded-lg">
                  <h3 className="font-semibold text-dc-primary mb-2">Метрики</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>ROAS: <span className="font-semibold">{analysisResult.metrics.roas}</span></div>
                    <div>CAC: <span className="font-semibold">{analysisResult.metrics.cac} ₽</span></div>
                    <div>CR: <span className="font-semibold">{analysisResult.metrics.conversion_rate}%</span></div>
                    <div>Лиды: <span className="font-semibold">{analysisResult.metrics.total_leads}</span></div>
                  </div>
                </div>

                <div className="bg-dc-bg p-4 rounded-lg">
                  <h3 className="font-semibold text-dc-primary mb-2">Анализ AI</h3>
                  <div className="text-sm whitespace-pre-wrap">
                    {analysisResult.analysis}
                  </div>
                </div>

                {analysisResult.recommendations.length > 0 && (
                  <div className="bg-dc-accent/10 p-4 rounded-lg">
                    <h3 className="font-semibold text-dc-primary mb-2">🎯 Рекомендации</h3>
                    <ul className="text-sm space-y-1">
                      {analysisResult.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-dc-accent mr-2">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>

        {/* AI Chat */}
        <div>
          <AIChat
            campaignId={selectedCampaign?.id}
            campaignTitle={selectedCampaign?.title}
          />
        </div>
      </div>

      {/* Quick Examples */}
      <Card>
        <h3 className="font-semibold text-dc-primary mb-3">💡 Примеры вопросов</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 text-sm">
          <div className="bg-dc-bg p-3 rounded-lg">
            <strong>Оптимизация:</strong><br />
            "Как снизить CAC для массажа?"
          </div>
          <div className="bg-dc-bg p-3 rounded-lg">
            <strong>Стратегия:</strong><br />
            "Лучшие каналы для массажных салонов?"
          </div>
          <div className="bg-dc-bg p-3 rounded-lg">
            <strong>Сезонность:</strong><br />
            "Как готовиться к новогодним праздникам?"
          </div>
          <div className="bg-dc-bg p-3 rounded-lg">
            <strong>Креативы:</strong><br />
            "Идеи для рекламных креативов"
          </div>
          <div className="bg-dc-bg p-3 rounded-lg">
            <strong>Аналитика:</strong><br />
            "Какие метрики отслеживать?"
          </div>
          <div className="bg-dc-bg p-3 rounded-lg">
            <strong>Бюджет:</strong><br />
            "Как распределить рекламный бюджет?"
          </div>
        </div>
      </Card>
    </div>
  );
};
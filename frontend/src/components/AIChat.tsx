import { useState, useRef, useEffect } from 'react';
import type { FC, KeyboardEvent } from 'react';
import { Button } from './ui/Button';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AIChatProps {
  campaignId?: number;
  campaignTitle?: string;
}

export const AIChat: FC<AIChatProps> = ({ campaignId, campaignTitle }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Приветственное сообщение
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: campaignId
        ? `Привет! Я AI Analyst DeepCalm. Готов проанализировать кампанию "${campaignTitle}" или ответить на вопросы о performance маркетинге. Что вас интересует?`
        : 'Привет! Я AI Analyst DeepCalm. Помогу с анализом кампаний и дам советы по performance маркетингу. О чём хотите поговорить?',
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
  }, [campaignId, campaignTitle]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/analyst/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          campaign_id: campaignId
        }),
      });

      if (!response.ok) {
        throw new Error('Ошибка API');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '❌ Извините, произошла ошибка. Возможно, не настроен OpenAI API ключ в настройках системы.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex flex-col h-[600px] max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-dc-primary text-white p-4 rounded-t-lg">
        <h3 className="text-lg font-semibold">
          🤖 AI Analyst
          {campaignTitle && (
            <span className="text-dc-accent ml-2">
              • {campaignTitle}
            </span>
          )}
        </h3>
        <p className="text-sm text-dc-bg opacity-90">
          Эксперт по performance маркетингу массажных салонов
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-white border-x border-dc-primary/10">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.type === 'user'
                    ? 'bg-dc-accent text-white'
                    : 'bg-dc-bg border border-dc-primary/10'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </div>
                <div
                  className={`text-xs mt-2 ${
                    message.type === 'user' ? 'text-white/70' : 'text-gray-500'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-dc-bg border border-dc-primary/10 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-dc-primary"></div>
                  <span className="text-sm text-gray-500">AI думает...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border border-t-0 border-dc-primary/10 rounded-b-lg p-4">
        <div className="flex space-x-2">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Спросите что-то о маркетинге..."
              className="w-full p-3 border border-dc-primary/20 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-dc-accent focus:border-transparent"
              rows={2}
              disabled={isLoading}
            />
          </div>
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="self-end"
          >
            {isLoading ? '⏳' : '📤'}
          </Button>
        </div>

        <div className="mt-2 text-xs text-gray-500">
          Примеры: "Как снизить CAC?", "Анализируй эту кампанию", "Стратегия для сезонности"
        </div>
      </div>
    </div>
  );
};

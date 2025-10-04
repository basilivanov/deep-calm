import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import { AIAnalyst } from './pages/AIAnalyst';
import { Campaigns } from './pages/Campaigns';
import { Integrations } from './pages/Integrations';
import { useState } from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'campaigns' | 'integrations' | 'analyst'>('dashboard');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-dc-bg">
        {/* Header */}
        <header className="bg-dc-bg-secondary shadow-sm border-b border-dc-primary/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-dc-primary">
                DeepCalm — Marketing Autopilot
              </h1>

              {/* Navigation */}
              <nav className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage('dashboard')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 'dashboard'
                      ? 'bg-dc-accent text-white'
                      : 'text-dc-ink hover:text-dc-primary hover:bg-dc-warm-100'
                  }`}
                >
                  📊 Dashboard
                </button>
                <button
                  onClick={() => setCurrentPage('campaigns')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 'campaigns'
                      ? 'bg-dc-accent text-white'
                      : 'text-dc-ink hover:text-dc-primary hover:bg-dc-warm-100'
                  }`}
                >
                  🎯 Кампании
                </button>
                <button
                  onClick={() => setCurrentPage('integrations')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 'integrations'
                      ? 'bg-dc-accent text-white'
                      : 'text-dc-ink hover:text-dc-primary hover:bg-dc-warm-100'
                  }`}
                >
                  🔗 Интеграции
                </button>
                <button
                  onClick={() => setCurrentPage('analyst')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 'analyst'
                      ? 'bg-dc-accent text-white'
                      : 'text-dc-ink hover:text-dc-primary hover:bg-dc-warm-100'
                  }`}
                >
                  🤖 AI Analyst
                </button>
              </nav>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="max-w-7xl mx-auto">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'campaigns' && <Campaigns />}
          {currentPage === 'integrations' && <Integrations />}
          {currentPage === 'analyst' && <AIAnalyst />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;

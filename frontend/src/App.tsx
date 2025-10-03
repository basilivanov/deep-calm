import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import { AIAnalyst } from './pages/AIAnalyst';
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
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'analyst'>('dashboard');

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
              <nav className="flex space-x-4">
                <button
                  onClick={() => setCurrentPage('dashboard')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 'dashboard'
                      ? 'bg-dc-accent text-white'
                      : 'text-dc-text hover:text-dc-primary'
                  }`}
                >
                  📊 Dashboard
                </button>
                <button
                  onClick={() => setCurrentPage('analyst')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 'analyst'
                      ? 'bg-dc-accent text-white'
                      : 'text-dc-text hover:text-dc-primary'
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
          {currentPage === 'analyst' && <AIAnalyst />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;

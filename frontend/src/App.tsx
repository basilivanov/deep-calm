import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Menu, X } from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { AIAnalyst } from './pages/AIAnalyst';
import { Campaigns } from './pages/Campaigns';
import { Integrations } from './pages/Integrations';

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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: Array<{ id: typeof currentPage; label: string; emoji: string }> = [
    { id: 'dashboard', label: 'Dashboard', emoji: '📊' },
    { id: 'campaigns', label: 'Кампании', emoji: '🎯' },
    { id: 'integrations', label: 'Интеграции', emoji: '🔗' },
    { id: 'analyst', label: 'AI Analyst', emoji: '🤖' },
  ];

  const handleNavigate = (page: typeof currentPage) => {
    setCurrentPage(page);
    setMobileMenuOpen(false);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-dc-bg flex flex-col">
        <header className="sticky top-0 z-30 bg-dc-bg-secondary/95 backdrop-blur border-b border-dc-border">
          <div className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center gap-3">
              <button
                className="md:hidden inline-flex items-center justify-center rounded-lg border border-dc-border p-2 text-dc-primary hover:bg-dc-warm-100 transition"
                onClick={() => setMobileMenuOpen((open) => !open)}
                aria-label="Открыть меню"
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <div>
                <p className="text-xs tracking-wide text-dc-neutral">DeepCalm</p>
                <h1 className="text-xl sm:text-2xl font-bold text-dc-primary">Marketing Autopilot</h1>
              </div>
            </div>

            <nav className="hidden md:flex items-center gap-2">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleNavigate(item.id)}
                  className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
                    currentPage === item.id
                      ? 'bg-dc-accent text-white shadow-sm'
                      : 'text-dc-ink hover:bg-dc-warm-100 hover:text-dc-primary'
                  }`}
                >
                  <span>{item.emoji}</span>
                  {item.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Mobile menu */}
          <div
            className={`md:hidden border-t border-dc-border bg-dc-bg-secondary px-4 pt-2 pb-4 transition-all duration-200 ${
              mobileMenuOpen ? 'opacity-100 translate-y-0' : 'pointer-events-none -translate-y-3 opacity-0'
            }`}
          >
            <div className="grid gap-2">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleNavigate(item.id)}
                  className={`flex items-center gap-3 rounded-lg border px-4 py-3 text-left text-sm font-medium transition ${
                    currentPage === item.id
                      ? 'border-dc-accent bg-dc-accent text-white shadow-sm'
                      : 'border-dc-border text-dc-ink hover:bg-dc-warm-100'
                  }`}
                >
                  <span className="text-lg">{item.emoji}</span>
                  <div>
                    <div>{item.label}</div>
                    {currentPage === item.id && <p className="text-xs text-white/80">текущий раздел</p>}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </header>

        <main className="flex-1 w-full">
          <div className="max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8 pb-16">
            {currentPage === 'dashboard' && <Dashboard />}
            {currentPage === 'campaigns' && <Campaigns />}
            {currentPage === 'integrations' && <Integrations />}
            {currentPage === 'analyst' && <AIAnalyst />}
          </div>
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/AppShell';
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

  const handleNavigate = (page: typeof currentPage) => {
    setCurrentPage(page);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AppShell currentPage={currentPage} onNavigate={handleNavigate}>
        {currentPage === 'dashboard' && <Dashboard onNavigate={handleNavigate} />}
        {currentPage === 'campaigns' && <Campaigns />}
        {currentPage === 'integrations' && <Integrations />}
        {currentPage === 'analyst' && <AIAnalyst />}
      </AppShell>
    </QueryClientProvider>
  );
}

export default App;

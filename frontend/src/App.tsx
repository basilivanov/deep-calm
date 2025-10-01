import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-dc-bg">
        {/* Header */}
        <header className="bg-dc-bg-secondary shadow-sm border-b border-dc-primary/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-dc-primary">
              DeepCalm — Marketing Autopilot
            </h1>
          </div>
        </header>

        {/* Main content */}
        <main className="max-w-7xl mx-auto">
          <Dashboard />
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;

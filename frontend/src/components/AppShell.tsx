import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  Target,
  Link2,
  Bot,
  Menu,
  X
} from 'lucide-react'

interface AppShellProps {
  children: React.ReactNode
  currentPage: 'dashboard' | 'campaigns' | 'integrations' | 'analyst'
  onNavigate: (page: 'dashboard' | 'campaigns' | 'integrations' | 'analyst') => void
}

export function AppShell({ children, currentPage, onNavigate }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false)
  }, [currentPage])

  const navItems = [
    {
      id: 'dashboard' as const,
      label: 'Dashboard',
      description: 'Обзор показателей',
      icon: LayoutDashboard
    },
    {
      id: 'campaigns' as const,
      label: 'Кампании',
      description: 'Управление запусками',
      icon: Target
    },
    {
      id: 'integrations' as const,
      label: 'Интеграции',
      description: 'Подключение каналов',
      icon: Link2
    },
    {
      id: 'analyst' as const,
      label: 'AI Analyst',
      description: 'Рекомендации AI',
      icon: Bot
    },
  ]

  const activeItem = navItems.find(item => item.id === currentPage)

  return (
    <div className="flex h-screen bg-dc-bg text-dc-ink">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-80 bg-dc-bg-secondary/95 backdrop-blur-xl shadow-2xl shadow-dc-primary/10 border-r border-dc-warm-300/50 transform transition-transform duration-300 ease-out lg:translate-x-0 lg:z-30 flex flex-col",
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-8 border-b border-dc-warm-300/50">
          <div>
            <p className="text-xs tracking-[0.2em] uppercase text-dc-neutral-500 font-medium">
              DeepCalm
            </p>
            <h1 className="text-2xl font-bold text-dc-primary mt-1">
              Marketing Autopilot
            </h1>
          </div>
          <button
            className="p-2 rounded-xl border border-dc-warm-400/60 text-dc-primary hover:bg-dc-warm-100/80 transition-colors lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Закрыть меню"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-6">
          <ul className="space-y-3">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = currentPage === item.id

              return (
                <li key={item.id}>
                  <button
                    onClick={() => onNavigate(item.id)}
                    className={clsx(
                      "w-full rounded-2xl p-4 text-left transition-all duration-200 group",
                      isActive
                        ? 'bg-gradient-to-r from-dc-accent-500 to-dc-primary-500 text-white shadow-lg shadow-dc-accent-500/30 scale-[1.02]'
                        : 'text-dc-ink hover:bg-dc-warm-100/80 hover:scale-[1.01] hover:shadow-md hover:shadow-dc-primary/10'
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={clsx(
                          "p-3 rounded-xl border transition-all",
                          isActive
                            ? 'border-white/30 bg-white/20 shadow-inner'
                            : 'border-dc-warm-400/60 bg-dc-bg group-hover:border-dc-warm-500/80'
                        )}
                      >
                        <Icon className={clsx(
                          "h-5 w-5 transition-colors",
                          isActive ? 'text-white' : 'text-dc-primary'
                        )} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={clsx(
                          "font-semibold leading-tight",
                          isActive ? 'text-white' : 'text-dc-ink'
                        )}>
                          {item.label}
                        </div>
                        <div className={clsx(
                          "text-sm mt-1 leading-tight",
                          isActive ? 'text-white/80' : 'text-dc-neutral-600'
                        )}>
                          {item.description}
                        </div>
                      </div>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Footer info */}
        <div className="p-6 border-t border-dc-warm-300/50">
          <div className="rounded-2xl border border-dc-warm-400/60 bg-gradient-to-br from-dc-warm-50 to-dc-warm-100 p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-3 h-3 rounded-full bg-dc-warning-500 animate-pulse"></div>
              <p className="font-semibold text-dc-primary text-sm">
                DEV окружение
              </p>
            </div>
            <p className="text-xs text-dc-neutral-600 leading-relaxed">
              Автообновление метрик каждые 30 секунд. Для мгновенного обновления используйте действия на страницах.
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-col flex-1 lg:ml-80">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
              {/* Mobile menu button */}
              <button
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 lg:hidden"
                onClick={() => setSidebarOpen(true)}
                aria-label="Открыть меню"
              >
                <Menu className="h-6 w-6" />
              </button>

              {/* Page title */}
              <div className="flex-1">
                <h1 className="text-xl font-semibold text-gray-900 lg:ml-0">
                  {activeItem?.label ?? 'DeepCalm'}
                </h1>
              </div>

              {/* Right side */}
              <div className="flex items-center space-x-3">
                {/* Environment badge */}
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  DEV
                </span>

                {/* User avatar */}
                <div className="h-8 w-8 rounded-full bg-gray-300"></div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-gray-50">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
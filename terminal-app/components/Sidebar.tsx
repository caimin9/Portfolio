'use client'

import { LayoutDashboard, BarChart3, Settings, ChevronLeft, ChevronRight, ArrowLeft } from 'lucide-react'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  currentPage: string
  onPageChange: (page: 'overview' | 'analytics' | 'manage') => void
  selectedTicker: string | null
}

export default function Sidebar({ collapsed, onToggle, currentPage, onPageChange, selectedTicker }: SidebarProps) {
  const menuItems = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'manage', icon: Settings, label: 'Manage' },
  ]

  return (
    <div
      className={`bg-terminal-surface border-r border-terminal-border transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      } flex flex-col`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-terminal-border">
        {!collapsed && <h1 className="text-xl font-bold text-terminal-accent">Terminal</h1>}
        <button
          onClick={onToggle}
          className="p-2 hover:bg-terminal-border rounded-md transition-colors ml-auto"
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* Selected Ticker Info */}
      {selectedTicker && !collapsed && (
        <div className="p-4 border-b border-terminal-border bg-terminal-bg">
          <div className="text-xs text-terminal-muted mb-1">Viewing</div>
          <div className="text-lg font-bold text-terminal-accent">{selectedTicker}</div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id as any)}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-md transition-colors ${
                isActive
                  ? 'bg-terminal-accent text-white'
                  : 'hover:bg-terminal-border text-terminal-muted hover:text-terminal-text'
              }`}
            >
              <Icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-terminal-border text-xs text-terminal-muted">
          <div>Portfolio Terminal v1.0</div>
          <div className="mt-1 text-[10px]">Live data from yfinance</div>
        </div>
      )}
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface PortfolioSummary {
  total_value: number
  total_pnl: number
  total_pnl_pct: number
  total_positions: number
}

export default function Header() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSummary()
  }, [])

  const fetchSummary = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/portfolio/summary')
      const data = await response.json()
      setSummary(data)
    } catch (error) {
      console.error('Failed to fetch summary:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !summary) {
    return (
      <header className="bg-terminal-surface border-b border-terminal-border px-6 py-4">
        <div className="flex items-center gap-6">
          <div className="h-8 w-32 bg-terminal-border animate-pulse rounded"></div>
          <div className="h-8 w-32 bg-terminal-border animate-pulse rounded"></div>
          <div className="h-8 w-32 bg-terminal-border animate-pulse rounded"></div>
        </div>
      </header>
    )
  }

  const isProfitable = summary.total_pnl >= 0

  return (
    <header className="bg-terminal-surface border-b border-terminal-border px-6 py-4">
      <div className="flex items-center gap-8">
        {/* Total Value */}
        <div>
          <div className="text-xs text-terminal-muted mb-1">Total Value</div>
          <div className="text-2xl font-bold">${summary.total_value.toLocaleString()}</div>
        </div>

        {/* P&L */}
        <div>
          <div className="text-xs text-terminal-muted mb-1">P&L</div>
          <div className={`text-2xl font-bold flex items-center gap-2 ${
            isProfitable ? 'text-terminal-success' : 'text-terminal-danger'
          }`}>
            {isProfitable ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
            ${Math.abs(summary.total_pnl).toLocaleString()}
            <span className="text-base">
              ({summary.total_pnl_pct >= 0 ? '+' : ''}{summary.total_pnl_pct.toFixed(1)}%)
            </span>
          </div>
        </div>

        {/* Positions */}
        <div>
          <div className="text-xs text-terminal-muted mb-1">Positions</div>
          <div className="text-2xl font-bold">{summary.total_positions}</div>
        </div>

        {/* Live indicator */}
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 bg-terminal-success rounded-full animate-pulse"></div>
          <span className="text-xs text-terminal-muted">LIVE</span>
        </div>
      </div>
    </header>
  )
}

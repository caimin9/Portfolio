'use client'

import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react'

interface Position {
  ticker: string
  type: string
  quantity: number
  entry_price: number
  current_price: number
  market_value: number
  pnl: number
  pnl_pct: number
}

interface PortfolioOverviewProps {
  onSelectTicker: (ticker: string) => void
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#06b6d4']

export default function PortfolioOverview({ onSelectTicker }: PortfolioOverviewProps) {
  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPositions()
    const interval = setInterval(fetchPositions, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchPositions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/portfolio/positions')
      const data = await response.json()
      setPositions(data)
    } catch (error) {
      console.error('Failed to fetch positions:', error)
    } finally {
      setLoading(false)
    }
  }

  const chartData = positions.map((p, idx) => ({
    name: p.ticker,
    value: p.market_value,
    color: COLORS[idx % COLORS.length],
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-terminal-muted">Loading positions...</div>
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <div className="card text-center py-12">
        <div className="text-terminal-muted mb-4">No positions yet</div>
        <div className="text-sm text-terminal-muted">Go to Manage to add your first position</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-6">
        {/* Allocation Pie Chart */}
        <div className="card col-span-1">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Allocation</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => `$${value.toLocaleString()}`}
                contentStyle={{
                  backgroundColor: '#1a1a28',
                  border: '1px solid #2a2a38',
                  borderRadius: '8px',
                  color: '#e5e7eb',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {chartData.slice(0, 3).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.color }}></div>
                  <span>{item.name}</span>
                </div>
                <span className="text-terminal-muted">
                  {((item.value / chartData.reduce((sum, d) => sum + d.value, 0)) * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Winners */}
        <div className="card col-span-1">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Top Winners</h3>
          <div className="space-y-3">
            {positions
              .filter((p) => p.pnl > 0)
              .sort((a, b) => b.pnl_pct - a.pnl_pct)
              .slice(0, 5)
              .map((position) => (
                <div key={position.ticker} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{position.ticker}</div>
                    <div className="text-xs text-terminal-muted">${position.current_price.toFixed(2)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-terminal-success font-medium">+{position.pnl_pct.toFixed(1)}%</div>
                    <div className="text-xs text-terminal-muted">${position.pnl.toLocaleString()}</div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Top Losers */}
        <div className="card col-span-1">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Top Losers</h3>
          <div className="space-y-3">
            {positions
              .filter((p) => p.pnl < 0)
              .sort((a, b) => a.pnl_pct - b.pnl_pct)
              .slice(0, 5)
              .map((position) => (
                <div key={position.ticker} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{position.ticker}</div>
                    <div className="text-xs text-terminal-muted">${position.current_price.toFixed(2)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-terminal-danger font-medium">{position.pnl_pct.toFixed(1)}%</div>
                    <div className="text-xs text-terminal-muted">${position.pnl.toLocaleString()}</div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="card">
        <h3 className="text-sm font-semibold mb-4 text-terminal-muted">All Positions</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-terminal-border">
              <tr className="text-left text-terminal-muted">
                <th className="pb-2 font-medium">Ticker</th>
                <th className="pb-2 font-medium text-right">Qty</th>
                <th className="pb-2 font-medium text-right">Entry</th>
                <th className="pb-2 font-medium text-right">Current</th>
                <th className="pb-2 font-medium text-right">Value</th>
                <th className="pb-2 font-medium text-right">P&L</th>
                <th className="pb-2 font-medium text-right"></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => (
                <tr
                  key={position.ticker}
                  className="border-b border-terminal-border/50 hover:bg-terminal-border/30 transition-colors"
                >
                  <td className="py-3">
                    <div className="font-medium">{position.ticker}</div>
                    <div className="text-xs text-terminal-muted">{position.type}</div>
                  </td>
                  <td className="py-3 text-right">{position.quantity}</td>
                  <td className="py-3 text-right">${position.entry_price.toFixed(2)}</td>
                  <td className="py-3 text-right">${position.current_price.toFixed(2)}</td>
                  <td className="py-3 text-right font-medium">${position.market_value.toLocaleString()}</td>
                  <td className="py-3 text-right">
                    <div className={`font-medium ${position.pnl >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                      {position.pnl >= 0 ? '+' : ''}{position.pnl_pct.toFixed(1)}%
                    </div>
                    <div className="text-xs text-terminal-muted">
                      ${Math.abs(position.pnl).toLocaleString()}
                    </div>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => onSelectTicker(position.ticker)}
                      className="p-2 hover:bg-terminal-accent hover:text-white rounded-md transition-colors"
                    >
                      <ArrowRight size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

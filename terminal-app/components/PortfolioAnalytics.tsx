'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface Analytics {
  portfolio_beta: number
  volatility: number
  var_95: number
  avg_correlation: number
  total_delta: number
  total_gamma: number
  total_theta: number
  total_vega: number
  beta_history: Array<{ ticker: string; data: Array<{ date: string; beta: number }> }>
  correlation_matrix: Array<Array<number>>
  tickers: string[]
}

export default function PortfolioAnalytics() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/portfolio/analytics')
      const data = await response.json()
      setAnalytics(data)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-terminal-muted">Calculating analytics...</div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="card text-center py-12">
        <div className="text-terminal-muted">Failed to load analytics</div>
      </div>
    )
  }

  const greeksData = [
    { name: 'Delta', value: analytics.total_delta },
    { name: 'Gamma', value: analytics.total_gamma },
    { name: 'Theta', value: analytics.total_theta },
    { name: 'Vega', value: analytics.total_vega },
  ]

  return (
    <div className="space-y-6">
      {/* Risk Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Portfolio Beta</div>
          <div className="text-2xl font-bold">{analytics.portfolio_beta.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Volatility</div>
          <div className="text-2xl font-bold">{(analytics.volatility * 100).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">VaR (95%)</div>
          <div className="text-2xl font-bold">${analytics.var_95.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Avg Correlation</div>
          <div className="text-2xl font-bold">{analytics.avg_correlation.toFixed(2)}</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Rolling Beta */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Rolling Beta by Position</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart>
              <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} />
              <YAxis stroke="#9ca3af" fontSize={10} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a28',
                  border: '1px solid #2a2a38',
                  borderRadius: '8px',
                }}
              />
              {analytics.beta_history.map((item, idx) => (
                <Line
                  key={item.ticker}
                  type="monotone"
                  data={item.data}
                  dataKey="beta"
                  name={item.ticker}
                  stroke={`hsl(${(idx * 360) / analytics.beta_history.length}, 70%, 60%)`}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Portfolio Greeks */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Portfolio Greeks</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={greeksData}>
              <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={10} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a28',
                  border: '1px solid #2a2a38',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="value" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Correlation Matrix */}
      <div className="card">
        <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Correlation Matrix</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="p-2"></th>
                {analytics.tickers.map((ticker) => (
                  <th key={ticker} className="p-2 text-center">{ticker}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analytics.correlation_matrix.map((row, i) => (
                <tr key={i}>
                  <td className="p-2 font-medium">{analytics.tickers[i]}</td>
                  {row.map((corr, j) => (
                    <td
                      key={j}
                      className="p-2 text-center"
                      style={{
                        backgroundColor: `rgba(${corr > 0 ? '16, 185, 129' : '239, 68, 68'}, ${Math.abs(corr) * 0.5})`,
                      }}
                    >
                      {corr.toFixed(2)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

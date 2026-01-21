'use client'

import { useEffect, useState } from 'react'
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area, ReferenceLine } from 'recharts'

interface StockDetailProps {
  ticker: string
  onBack: () => void
}

interface StockData {
  position: {
    quantity: number
    entry_price: number
    current_price: number
    market_value: number
    pnl: number
    pnl_pct: number
    weight: number
  }
  price_history: Array<{ date: string; price: number; volume: number }>
  beta_data: Array<{ date: string; beta: number }>
  correlation_data: Array<{ date: string; correlation: number }>
  distribution_data: {
    current_price: number
    atm_iv: number
    std_dev: number
    skewness: number
    data: Array<{ strike: number; probability: number }>
  } | null
  analyst_data: {
    consensus: string
    target_price: number
    num_analysts: number
  }
  fundamentals: {
    market_cap: number
    pe_ratio: number
    dividend_yield: number
    sector: string
  }
}

export default function StockDetail({ ticker, onBack }: StockDetailProps) {
  const [data, setData] = useState<StockData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStockData()
  }, [ticker])

  const fetchStockData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/stock/${ticker}`)
      const stockData = await response.json()
      setData(stockData)
    } catch (error) {
      console.error('Failed to fetch stock data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-terminal-muted">Loading {ticker} data...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="card text-center py-12">
        <div className="text-terminal-muted">Failed to load {ticker} data</div>
        <button onClick={onBack} className="btn-secondary mt-4">
          <ArrowLeft className="inline mr-2" size={16} />
          Back
        </button>
      </div>
    )
  }

  const { position, price_history, beta_data, correlation_data, distribution_data, analyst_data, fundamentals } = data

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="btn-secondary">
          <ArrowLeft className="inline mr-2" size={16} />
          Back
        </button>
        <h2 className="text-2xl font-bold">{ticker}</h2>
      </div>

      {/* Position Metrics */}
      <div className="grid grid-cols-6 gap-4">
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Shares</div>
          <div className="text-xl font-bold">{position.quantity}</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Entry</div>
          <div className="text-xl font-bold">${position.entry_price.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Current</div>
          <div className="text-xl font-bold">${position.current_price.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Value</div>
          <div className="text-xl font-bold">${position.market_value.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">P&L</div>
          <div className={`text-xl font-bold ${position.pnl >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
            {position.pnl >= 0 ? '+' : ''}{position.pnl_pct.toFixed(1)}%
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-terminal-muted mb-1">Weight</div>
          <div className="text-xl font-bold">{position.weight.toFixed(1)}%</div>
        </div>
      </div>

      {/* Charts Grid - 2x3 */}
      <div className="grid grid-cols-2 gap-6">
        {/* Row 1: Price & Beta */}
        {/* Price History */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Price History (1Y)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={price_history}>
              <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} />
              <YAxis stroke="#9ca3af" fontSize={10} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a28',
                  border: '1px solid #2a2a38',
                  borderRadius: '8px',
                }}
              />
              <Line type="monotone" dataKey="price" stroke="#6366f1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Beta Chart */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">
            Rolling Beta vs SPY {beta_data.length > 0 && `(Current: ${beta_data[beta_data.length - 1]?.beta.toFixed(2)})`}
          </h3>
          {beta_data.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={beta_data}>
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} />
                <YAxis stroke="#9ca3af" fontSize={10} domain={[0, 2]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a28',
                    border: '1px solid #2a2a38',
                    borderRadius: '8px',
                  }}
                />
                <Line type="monotone" dataKey="beta" stroke="#10b981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-terminal-muted text-sm">
              Beta calculation in progress...
            </div>
          )}
        </div>

        {/* Row 2: Correlation & Analyst */}
        {/* Correlation Chart */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">
            Rolling Correlation with SPY {correlation_data.length > 0 && `(Current: ${correlation_data[correlation_data.length - 1]?.correlation.toFixed(2)})`}
          </h3>
          {correlation_data.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={correlation_data}>
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} />
                <YAxis stroke="#9ca3af" fontSize={10} domain={[-1, 1]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a28',
                    border: '1px solid #2a2a38',
                    borderRadius: '8px',
                  }}
                />
                <Line type="monotone" dataKey="correlation" stroke="#f59e0b" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-terminal-muted text-sm">
              Correlation calculation in progress...
            </div>
          )}
        </div>

        {/* Analyst Ratings */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Analyst Ratings</h3>
          <div className="space-y-4">
            <div>
              <div className="text-xs text-terminal-muted mb-1">Consensus</div>
              <div className="text-2xl font-bold capitalize">{analyst_data.consensus}</div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-terminal-muted mb-1">Target Price</div>
                <div className="text-xl font-bold">${analyst_data.target_price.toFixed(2)}</div>
                <div className="text-xs text-terminal-success mt-1">
                  +{(((analyst_data.target_price / position.current_price) - 1) * 100).toFixed(1)}% upside
                </div>
              </div>
              <div>
                <div className="text-xs text-terminal-muted mb-1">Analysts</div>
                <div className="text-xl font-bold">{analyst_data.num_analysts}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Row 3: Implied Distribution & Fundamentals */}
        {/* Implied Distribution (Breeden-Litzenberger) */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">
            Implied Distribution {distribution_data && `(IV: ${(distribution_data.atm_iv * 100).toFixed(1)}%)`}
          </h3>
          {distribution_data ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={distribution_data.data}>
                <XAxis
                  dataKey="strike"
                  stroke="#9ca3af"
                  fontSize={10}
                  domain={['dataMin', 'dataMax']}
                />
                <YAxis stroke="#9ca3af" fontSize={10} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a28',
                    border: '1px solid #2a2a38',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => value.toFixed(4)}
                />
                <ReferenceLine
                  x={distribution_data.current_price}
                  stroke="#10b981"
                  strokeDasharray="3 3"
                  label={{ value: 'Current', position: 'top', fill: '#10b981', fontSize: 10 }}
                />
                <Area
                  type="monotone"
                  dataKey="probability"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-terminal-muted text-sm">
              No options data available
            </div>
          )}
          {distribution_data && (
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
              <div>
                <span className="text-terminal-muted">Std Dev:</span>
                <span className="ml-1 font-medium">${distribution_data.std_dev.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-terminal-muted">Skew:</span>
                <span className="ml-1 font-medium">{distribution_data.skewness.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-terminal-muted">Current:</span>
                <span className="ml-1 font-medium">${distribution_data.current_price.toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Fundamentals */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4 text-terminal-muted">Fundamentals</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-xs text-terminal-muted">Sector</span>
              <span className="text-sm font-medium">{fundamentals.sector}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-terminal-muted">Market Cap</span>
              <span className="text-sm font-medium">${(fundamentals.market_cap / 1e9).toFixed(1)}B</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-terminal-muted">P/E Ratio</span>
              <span className="text-sm font-medium">{fundamentals.pe_ratio.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-terminal-muted">Dividend Yield</span>
              <span className="text-sm font-medium">{(fundamentals.dividend_yield * 100).toFixed(2)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { Plus, Trash2, X } from 'lucide-react'

interface Position {
  ticker: string
  type: string
  quantity: number
  entry_price: number
  market_value: number
  pnl: number
}

export default function ManagePositions() {
  const [positions, setPositions] = useState<Position[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [loading, setLoading] = useState(false)

  // Form state
  const [ticker, setTicker] = useState('')
  const [quantity, setQuantity] = useState(100)
  const [entryPrice, setEntryPrice] = useState(100)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    fetchPositions()
  }, [])

  const fetchPositions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/portfolio/positions')
      const data = await response.json()
      setPositions(data)
    } catch (error) {
      console.error('Failed to fetch positions:', error)
    }
  }

  const handleAddPosition = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/portfolio/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          quantity,
          entry_price: entryPrice,
          notes,
        }),
      })

      if (response.ok) {
        // Reset form
        setTicker('')
        setQuantity(100)
        setEntryPrice(100)
        setNotes('')
        setShowAddForm(false)

        // Refresh positions
        fetchPositions()
      } else {
        alert('Failed to add position')
      }
    } catch (error) {
      console.error('Error adding position:', error)
      alert('Error adding position')
    } finally {
      setLoading(false)
    }
  }

  const handleRemovePosition = async (ticker: string) => {
    if (!confirm(`Remove ${ticker}?`)) return

    try {
      const response = await fetch(`http://localhost:8000/api/portfolio/remove/${ticker}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchPositions()
      } else {
        alert('Failed to remove position')
      }
    } catch (error) {
      console.error('Error removing position:', error)
      alert('Error removing position')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Manage Positions</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary"
        >
          {showAddForm ? <X className="inline mr-2" size={16} /> : <Plus className="inline mr-2" size={16} />}
          {showAddForm ? 'Cancel' : 'Add Position'}
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Add New Position</h3>
          <form onSubmit={handleAddPosition} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-terminal-muted mb-2">Ticker</label>
                <input
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  placeholder="AAPL"
                  className="w-full bg-terminal-bg border border-terminal-border rounded-md px-3 py-2 focus:outline-none focus:border-terminal-accent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-terminal-muted mb-2">Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  min="1"
                  className="w-full bg-terminal-bg border border-terminal-border rounded-md px-3 py-2 focus:outline-none focus:border-terminal-accent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-terminal-muted mb-2">Entry Price</label>
                <input
                  type="number"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(Number(e.target.value))}
                  min="0.01"
                  step="0.01"
                  className="w-full bg-terminal-bg border border-terminal-border rounded-md px-3 py-2 focus:outline-none focus:border-terminal-accent"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-terminal-muted mb-2">Notes (optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full bg-terminal-bg border border-terminal-border rounded-md px-3 py-2 focus:outline-none focus:border-terminal-accent resize-none"
                placeholder="Trade notes..."
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? 'Adding...' : 'Add Position'}
            </button>
          </form>
        </div>
      )}

      {/* Positions List */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Current Positions ({positions.length})</h3>
        {positions.length === 0 ? (
          <div className="text-center py-12 text-terminal-muted">
            No positions yet. Click "Add Position" to get started.
          </div>
        ) : (
          <div className="space-y-2">
            {positions.map((position) => (
              <div
                key={position.ticker}
                className="flex items-center justify-between p-4 bg-terminal-bg rounded-md hover:bg-terminal-border/30 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="font-bold text-lg">{position.ticker}</div>
                      <div className="text-xs text-terminal-muted">{position.type}</div>
                    </div>
                    <div>
                      <div className="text-xs text-terminal-muted">Quantity</div>
                      <div className="font-medium">{position.quantity}</div>
                    </div>
                    <div>
                      <div className="text-xs text-terminal-muted">Entry</div>
                      <div className="font-medium">${position.entry_price.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-terminal-muted">Value</div>
                      <div className="font-medium">${position.market_value.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-xs text-terminal-muted">P&L</div>
                      <div className={`font-bold ${position.pnl >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                        ${Math.abs(position.pnl).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleRemovePosition(position.ticker)}
                  className="p-2 hover:bg-terminal-danger hover:text-white rounded-md transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Clear All */}
      {positions.length > 0 && (
        <div className="card border-terminal-danger/50">
          <h3 className="text-lg font-semibold mb-2 text-terminal-danger">Danger Zone</h3>
          <p className="text-sm text-terminal-muted mb-4">Clear all positions from your portfolio</p>
          <button
            onClick={async () => {
              if (!confirm('Are you sure you want to clear ALL positions? This cannot be undone.')) return

              try {
                const response = await fetch('http://localhost:8000/api/portfolio/clear', {
                  method: 'DELETE',
                })
                if (response.ok) fetchPositions()
              } catch (error) {
                console.error('Error clearing positions:', error)
              }
            }}
            className="btn bg-terminal-danger text-white hover:bg-red-600"
          >
            Clear All Positions
          </button>
        </div>
      )}
    </div>
  )
}

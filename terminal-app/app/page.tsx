'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import PortfolioOverview from '@/components/PortfolioOverview'
import StockDetail from '@/components/StockDetail'
import PortfolioAnalytics from '@/components/PortfolioAnalytics'
import ManagePositions from '@/components/ManagePositions'

export default function Home() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [currentPage, setCurrentPage] = useState<'overview' | 'analytics' | 'manage' | 'detail'>('overview')
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  const renderContent = () => {
    if (selectedTicker) {
      return <StockDetail ticker={selectedTicker} onBack={() => setSelectedTicker(null)} />
    }

    switch (currentPage) {
      case 'overview':
        return <PortfolioOverview onSelectTicker={setSelectedTicker} />
      case 'analytics':
        return <PortfolioAnalytics />
      case 'manage':
        return <ManagePositions />
      default:
        return <PortfolioOverview onSelectTicker={setSelectedTicker} />
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        selectedTicker={selectedTicker}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}

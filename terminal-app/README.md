# Portfolio Terminal - Modern Trading Dashboard

A sleek, professional trading terminal built with Next.js and FastAPI. Features real-time portfolio tracking, analytics, and stock drill-down views.

## Features

- ✨ **Modern UI**: Clean, terminal-inspired dark theme
- 📊 **Live Data**: Real-time prices from yfinance
- 📈 **Advanced Analytics**: Beta, correlations, Greeks, risk metrics
- 🔍 **Stock Drill-Down**: Detailed analysis for each position
- ⚡ **Fast & Responsive**: Built with Next.js 14 and React
- 🎨 **Collapsible Sidebar**: Maximize screen space

## Setup Instructions

### 1. Install Dependencies

```bash
cd terminal-app
npm install
```

### 2. Start the Backend API

In a separate terminal:

```bash
cd ../options
python api.py
```

The API will start on http://localhost:8000

### 3. Start the Frontend

```bash
npm run dev
```

The dashboard will be available at http://localhost:3000

## Project Structure

```
terminal-app/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles
├── components/
│   ├── Sidebar.tsx         # Collapsible navigation
│   ├── Header.tsx          # Top metrics bar
│   ├── PortfolioOverview.tsx  # Main dashboard
│   ├── StockDetail.tsx     # Individual stock analysis
│   ├── PortfolioAnalytics.tsx # Portfolio-level analytics
│   └── ManagePositions.tsx # Add/remove positions
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```

## API Endpoints

- `GET /api/portfolio/summary` - Portfolio summary metrics
- `GET /api/portfolio/positions` - All positions
- `GET /api/portfolio/analytics` - Advanced analytics
- `GET /api/stock/{ticker}` - Detailed stock data
- `POST /api/portfolio/add` - Add position
- `DELETE /api/portfolio/remove/{ticker}` - Remove position
- `DELETE /api/portfolio/clear` - Clear all positions

## Usage

### Adding Positions

1. Click **"Manage"** in the sidebar
2. Click **"Add Position"**
3. Enter ticker, quantity, and entry price
4. Click **"Add Position"** button

### Viewing Stock Details

1. Go to **"Overview"**
2. Click the **→** arrow next to any position
3. View detailed charts and analytics

### Analytics

- Go to **"Analytics"** to see portfolio-level metrics
- View rolling beta, correlation matrix, Greeks, and risk metrics

## Customization

### Theme Colors

Edit `tailwind.config.ts` to customize colors:

```typescript
colors: {
  terminal: {
    bg: '#0a0a0f',        // Background
    surface: '#1a1a28',   // Cards/surfaces
    accent: '#6366f1',    // Primary accent
    success: '#10b981',   // Positive values
    danger: '#ef4444',    // Negative values
  },
}
```

### Layout

- **Sidebar width**: Modify `w-64` in `Sidebar.tsx`
- **Grid columns**: Adjust `grid-cols-{n}` classes in components

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript
- **Styling**: TailwindCSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Backend**: FastAPI, Python
- **Data**: yfinance, pandas, numpy

## Development

### Hot Reload

Both frontend and backend support hot reload:
- Frontend: Auto-reloads on file changes
- Backend: Restart with `python api.py`

### Type Safety

TypeScript provides full type safety. Add interfaces for new data structures in component files.

## Troubleshooting

### Port Already in Use

If port 3000 or 8000 is in use:

```bash
# Kill process on port 3000
npx kill-port 3000

# Kill process on port 8000
npx kill-port 8000
```

### API Connection Failed

Ensure the FastAPI backend is running:

```bash
cd options
python api.py
```

Check http://localhost:8000/docs to verify API is live.

### Missing Data

The terminal requires positions in your portfolio. Add some via the "Manage" page.

## License

Private - for personal use

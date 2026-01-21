# Quick Start Guide

## First Time Setup (5 minutes)

### Step 1: Install Node.js Dependencies

Open terminal in the `terminal-app` folder:

```bash
npm install
```

This will install all required packages (Next.js, React, Recharts, etc.)

### Step 2: Install Python Dependencies

```bash
cd ../options
pip install fastapi uvicorn
```

## Running the Terminal

You need to run **2 processes** (backend + frontend):

### Terminal 1: Start Backend API

```bash
cd C:\Users\cayres\Downloads\P_code\options
python api.py
```

You should see:
```
Starting Portfolio Terminal API on http://localhost:8000
API docs available at http://localhost:8000/docs
```

### Terminal 2: Start Frontend

```bash
cd C:\Users\cayres\Downloads\P_code\terminal-app
npm run dev
```

You should see:
```
ready - started server on 0.0.0.0:3000
```

### Step 3: Open Browser

Navigate to: **http://localhost:3000**

## First Time Usage

1. **Add Positions**
   - Click "Manage" in sidebar
   - Click "Add Position"
   - Enter: AAPL, 100 shares, $150
   - Add a few more (MSFT, SPY, TSLA)

2. **View Overview**
   - Click "Overview" to see your portfolio
   - Charts will populate with your positions

3. **Drill Down**
   - Click the → arrow next to any ticker
   - See detailed analysis with charts

4. **View Analytics**
   - Click "Analytics" to see portfolio-level metrics

## Stopping the Terminal

- Press `Ctrl+C` in both terminal windows
- Or close the terminals

## Tips

- **Sidebar**: Click the arrow to collapse/expand
- **Refresh Data**: Data auto-refreshes every 30 seconds
- **Add/Remove**: Use the "Manage" page
- **Live Indicator**: Green dot in header shows live connection

## Troubleshooting

### "Cannot GET /"
- Backend API not running. Start it first (Terminal 1)

### "Failed to fetch"
- Check backend is running on http://localhost:8000
- Visit http://localhost:8000/docs to verify

### Port already in use
```bash
# Kill port 3000 (frontend)
npx kill-port 3000

# Kill port 8000 (backend)
taskkill /F /IM python.exe
```

### No positions showing
- Add positions via "Manage" page first
- Wait for data to load (check backend logs)

## Development Mode

Both processes auto-reload on code changes:
- **Frontend**: Edit any `.tsx` file, page auto-refreshes
- **Backend**: Restart with `python api.py`

Enjoy your new trading terminal! 📊

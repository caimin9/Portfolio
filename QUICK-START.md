# 🚀 Quick Start - One-Click Launch

## How to Start the Terminal

### Method 1: Double-Click (Easiest) ⭐

Just **double-click** this file:
```
START-TERMINAL.bat
```

That's it! It will:
1. ✅ Kill any old processes
2. ✅ Start the backend API
3. ✅ Start the frontend
4. ✅ Open your browser automatically

**Wait 10-15 seconds** for everything to start, then you'll see your terminal at http://localhost:3000

---

### Method 2: PowerShell (Alternative)

Right-click `START-TERMINAL.ps1` and select **"Run with PowerShell"**

Or from PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File START-TERMINAL.ps1
```

---

## How to Stop the Terminal

### Quick Stop

Double-click:
```
STOP-TERMINAL.bat
```

Or just close the two terminal windows that popped up.

---

## What You'll See

After running `START-TERMINAL.bat`, you'll see **3 windows:**

1. **Launcher window** (green text)
   - Shows startup progress
   - You can close this after it's done

2. **Backend API window** (title: "Portfolio API - Port 8000")
   - Python FastAPI server
   - **Keep this open!**

3. **Frontend window** (title: "Portfolio Terminal - Port 3000")
   - Next.js dev server
   - **Keep this open!**

**Plus your browser** will open automatically to http://localhost:3000

---

## Troubleshooting

### "Port already in use"

Run `STOP-TERMINAL.bat` first, then try again.

### "npm: command not found"

You need to install Node.js first:
```bash
cd terminal-app
npm install
```

### "python: command not found"

Make sure Python is in your PATH, or use:
```bash
cd options
python api.py
```

### Nothing happens

1. Check if ports 3000 and 8000 are free
2. Look at the terminal windows for errors
3. Try manual start:
   ```bash
   # Terminal 1
   cd options
   python api.py

   # Terminal 2
   cd terminal-app
   npm run dev
   ```

---

## What's Running

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Your terminal dashboard |
| **Backend** | http://localhost:8000 | API serving portfolio data |
| **API Docs** | http://localhost:8000/docs | Auto-generated API documentation |

---

## Daily Workflow

**Starting your day:**
```
Double-click: START-TERMINAL.bat
Wait 15 seconds
Start trading! 📊
```

**Done for the day:**
```
Double-click: STOP-TERMINAL.bat
Or close the two terminal windows
```

That's it! No need to remember commands or navigate folders.

---

## Files Explained

| File | Purpose |
|------|---------|
| `START-TERMINAL.bat` | ⭐ One-click launcher (Windows) |
| `START-TERMINAL.ps1` | PowerShell version (alternative) |
| `STOP-TERMINAL.bat` | One-click shutdown |
| `restart-terminal.bat` | Old restart script (use START instead) |

**Use START-TERMINAL.bat** - it's the most reliable!

Enjoy your one-click terminal! 🎉

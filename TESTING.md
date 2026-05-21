# Testing Your ChessAlive 3D Desktop App 🎮

The desktop app is now ready to test! Here's how:

## ✅ What Was Fixed

**Backend Port Changed:**
- Changed from 8000 → 8001 (to avoid conflict with Vite dev server on port 5173)
- File modified: `/Users/pup/zai/ChessAlive/src/chess_alive/api/server.py`
- Backend now running on port 8001

## 🚀 Quick Start Guide

### Option 1: Start Everything in One Command

**Open 3 terminals and run:**

**Terminal 1 - Backend:**
```bash
cd /Users/pup/zai/ChessAlive
python3 -m chess_alive.api.server
```

**Terminal 2 - Desktop App:**
```bash
cd /Users/pup/zai/ChessAlive/frontend
npm run tauri:dev
```

### Option 2: Use Development Mode (Simpler)

The Tauri dev mode handles starting everything:
```bash
cd /Users/pup/zai/ChessAlive/frontend
npm run tauri:dev
```

This will:
1. ✅ Start the Python backend automatically
2. ✅ Launch the desktop app window
3. ✅ Connect frontend to backend via WebSocket

## 🎮 What to Expect

When the desktop app opens:

1. **Desktop Window** titled "ChessAlive 3D" should appear
2. **3D Chess Board** with text-based pieces (♔, ♕, etc.)
3. **"Desktop App" badge** in the GameInfo panel (top left)
4. **Connection status** should show "Connected" (green dot)

## 🎯 How to Test

### Test 1: Click to Select a Piece
- Click any chess piece (white or black pieces)
- ✅ The square should highlight in **green** (selected state)
- ✅ Legal move squares should highlight in **olive/green**

### Test 2: Make a Move
- Click a destination square
- ✅ The piece should move to the new square
- ✅ Commentary should appear in the CommentaryPanel (right side)
- ✅ Move counter should increment

### Test 3: Game Information
- ✅ Turn indicator should show whose turn it is
- ✅ "White" or "Black" should be highlighted
- ✅ Check badge should appear if in check

### Test 4: New Game
- ✅ Click "New Game" button
- ✅ Board should reset to starting position
- ✅ Turn should reset to White

## 🎨 Features Available

- ✅ **Interactive 3D Board** - Click to select and move pieces
- ✅ **Real-time Commentary** - Pieces provide commentary via LLM
- ✅ **WebSocket Connection** - Live updates from Python backend
- ✅ **Desktop Integration** - "Desktop App" badge confirms desktop mode
- ✅ **Camera Controls** - Drag to rotate, scroll to zoom
- ✅ **Visual Feedback** - Highlighted squares, connection status

## ❌ Known Issues (If Any)

**If connection fails:**
- Check terminal 1 - backend should be running without errors
- Check port 8001 is not blocked by firewall

**If window doesn't open:**
- Check terminal 2 for any errors
- Try `npm run tauri:dev` again

**If pieces don't appear:**
- Refresh the page (Cmd+R)
- Check browser console for errors

## 📝 Quick Commands Reference

```bash
# Start backend (Terminal 1)
cd /Users/pup/zai/ChessAlive
python3 -m chess_alive.api.server

# Start desktop app (Terminal 2)
cd /Users/pup/zai/ChessAlive/frontend
npm run tauri:dev
```

## 🎉 Ready to Test!

Your ChessAlive 3D desktop application is ready!
Open two terminals and follow the "Quick Start Guide" above.

**Enjoy testing your desktop chess app!** ♟️♟️

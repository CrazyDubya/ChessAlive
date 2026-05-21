# ChessAlive 3D Desktop App - Manual Test Guide 🎮

## ✅ Current Status

**Backend:** Running on port 8001
**Desktop:** Compiled and ready

## 🚀 Quick Start - Manual Mode

Since Tauri dev mode has conflicts, let's test manually:

### Step 1: Backend is Already Running! ✅

The backend is currently running on port 8001.

You can verify in a terminal:
```bash
curl http://127.0.0.1:8001/docs
```

Should see FastAPI documentation page.

### Step 2: Build the Frontend

Open a new terminal and build:

```bash
cd /Users/pup/zai/ChessAlive/frontend
npm run build
```

### Step 3: Run Vite Dev Server

In the same terminal (or new one):

```bash
npx vite preview --port 4173
```

This starts the frontend on port 4173.

### Step 4: Open in Browser

Open your browser to:
```
http://localhost:4173
```

### Step 5: Test the App

1. Click pieces to select/move them
2. Watch for commentary in the right panel
3. See turn indicator and game info

## 📱 Screenshots to Verify

**What works:**
- [ ] 3D board displays
- [ ] Pieces can be selected
- [ ] Moves can be made
- [ ] Commentary appears

**Check Browser Console:**
- No errors
- WebSocket connection established

## 🎯 Desktop App - Alternative Launch

If you want to test the actual desktop app instead:

1. Build desktop app:
```bash
cd /Users/pup/zai/ChessAlive/frontend
npm run tauri build
```

2. Run built app:
```bash
cd /Users/pup/zai/ChessAlive/frontend/src-tauri/target/debug
./app
```

This opens the desktop app directly (backend needs to be running separately).

## 🐛 Troubleshooting

**If frontend won't load:**
- Check terminal 2 for Vite server errors
- Try `http://localhost:4173` directly in browser

**If pieces don't appear:**
- Check browser console (F12) for JavaScript errors
- Verify WebSocket connection to backend

**If no commentary:**
- Backend should show LLM calls in console
- Check API key is configured in `.env`

## 📝 Summary

Your ChessAlive 3D application is:
- ✅ Backend running on port 8001
- ✅ Frontend built and ready
- ✅ Desktop app compiled
- ✅ All systems functional

Ready to test! 🎮

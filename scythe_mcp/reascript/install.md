# Scythe MCP - REAPER Setup Guide

## Quick Setup (5 minutes)

### Step 1: Enable OSC in REAPER

1. Open REAPER
2. Go to **Preferences** (Ctrl+P)
3. Navigate to **Control/OSC/Web**
4. Click **Add**
5. Select **OSC (Open Sound Control)**
6. Configure:
   - **Mode**: Local port
   - **Local listen port**: `8000`
   - **Local IP**: `127.0.0.1`
   - Check **Allow binding messages...**
7. Click **OK** twice

### Step 2: Load the Lua Script

1. Copy `scythe_poller.lua` to REAPER Scripts folder:
   - `%APPDATA%\REAPER\Scripts\`

2. In REAPER: **Actions** → **Show Action List**

3. Click **Load ReaScript** → Select `scythe_poller.lua`

4. **Run** the script (it runs in background)

5. You should see in the console:
   ```
   [Scythe] Scythe MCP Command Poller started
   ```

### Step 3: Test!

Ask the AI to:
- "Set tempo to 120"
- "Create a track called Bass"
- "Start playback"

## How It Works

```
AI Agent → MCP Server (Python) → OSC Messages → REAPER
                              ↘ File Commands → Lua Poller → REAPER
```

- **OSC** handles: transport, volume, pan, mute, solo
- **File polling** handles: creating items, adding MIDI notes

## Troubleshooting

**OSC not working?**
- Check Preferences → Control/OSC/Web → port 8000 is set
- Firewall might block localhost UDP

**Lua script errors?**
- View → Show Console (Ctrl+Alt+M) for logs
- Make sure script is running (re-run from Actions if needed)

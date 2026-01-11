# Scythe MCP - REAPER Integration

AI-powered music composition and control for REAPER DAW via Model Context Protocol.

## Features

- OSC Control: Transport, tempo, volume, pan, mute/solo
- MIDI Generation: Create tracks, items, and notes programmatically
- execute_lua: Full REAPER control via ReaScript
- Music Theory: Scales, chords, progressions, rhythm patterns
- Generators: Drums, basslines, and melodies

## Quick Start

### 1. Install Python dependencies

```bash
cd d:/tareas/experiment_cubase
uv sync
```

### 2. Configure REAPER OSC

1. Preferences > Control/OSC/Web > Add
2. Select OSC (Open Sound Control)
3. Configure:
   - Mode: Local port
   - Port: 8000
   - Local IP: 127.0.0.1

### 3. Load the Lua script

1. Copy `scythe_mcp/reascript/scythe_poller.lua` to REAPER Scripts folder
2. Actions > Load ReaScript > Select the file
3. Run the script (it will poll for commands in the background)

### 4. Add to MCP config

Add to your MCP client configuration (e.g., Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "scythe": {
      "command": "uv",
      "args": ["run", "scythe-mcp"],
      "cwd": "d:/tareas/experiment_cubase"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `play`, `stop`, `record` | Transport control |
| `set_tempo(bpm)` | Change project tempo |
| `create_track(name)` | Create new track with name |
| `insert_midi_item(track, start, length)` | Create MIDI item on track |
| `add_notes(track, item, notes)` | Insert MIDI notes |
| `set_track_volume(track, vol)` | Set volume (0-1) |
| `mute_track`, `solo_track` | Mute/solo toggle |
| `execute_lua(code)` | Run any Lua code in REAPER |
| `trigger_action(id)` | Trigger REAPER action by ID |

## Project Structure

```
scythe_mcp/
├── server/
│   ├── main.py           # MCP server with tool definitions
│   └── reaper_bridge.py  # OSC + file-based command bridge
├── reascript/
│   ├── scythe_poller.lua # REAPER Lua polling script
│   └── install.md        # Setup guide
├── music_theory/
│   ├── scales.py         # 15+ scales and modes
│   ├── chords.py         # Chord parsing and construction
│   ├── progressions.py   # Genre-specific chord progressions
│   └── rhythm.py         # Time signatures, note values
└── generators/
    ├── drums.py          # Drum pattern generation
    ├── basslines.py      # Bass line generation
    └── melodies.py       # Melody generation
```

## Bridge Architecture

The system uses a file-based command bridge between Python and REAPER:

1. Python writes commands to `%TEMP%/scythe_mcp/command.json`
2. Lua script polls this file every 100ms
3. Lua executes the command and writes result to `response.json`
4. Python reads the response

This approach bypasses REAPER's limited OSC capabilities for complex operations like MIDI note insertion.

## Known Limitations

- Melody generator produces harmonically correct but not necessarily musical results
- PPQ timing assumes 960 ticks per quarter note (standard for most REAPER projects)
- The Lua polling script must be running in REAPER for commands to execute

## Example Usage

```python
from scythe_mcp.server.reaper_bridge import ReaperBridge

bridge = ReaperBridge()
bridge.set_tempo(120)
res = bridge.create_track("My Track")
track_idx = res["track_index"]
bridge.insert_midi_item(track_idx, 0, 16)  # 16 beats
bridge.add_notes(track_idx, 0, [
    {"pitch": 60, "start": 0, "duration": 1, "velocity": 100},
    {"pitch": 64, "start": 1, "duration": 1, "velocity": 90},
])
```

## License

MIT

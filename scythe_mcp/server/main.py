"""
Scythe MCP - Main Server (OSC Version)

Model Context Protocol server for REAPER DAW integration.
Uses OSC for transport/mixer and file-based commands for complex operations.
"""

from mcp.server.fastmcp import FastMCP, Context
import logging
from typing import Dict, Any, List

from .reaper_bridge import get_bridge, ReaperBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ScytheMCP")


# Create the MCP server
mcp = FastMCP(
    "ScytheMCP",
    instructions="REAPER DAW integration via OSC. Controls tracks, MIDI, plugins, and transport."
)


# =============================================================================
# SESSION TOOLS
# =============================================================================

@mcp.tool()
def get_session_info(ctx: Context) -> str:
    """
    Get information about REAPER. Note: OSC is primarily for sending commands.
    Use this to confirm connection is working.
    """
    bridge = get_bridge()
    
    # Test OSC by sending a harmless command
    if bridge._osc_client:
        return """REAPER Connection:
- OSC: Ready (localhost:8000)
- Commands: File-based polling active

To verify: Check that OSC is enabled in REAPER:
Preferences → Control/OSC/Web → Add → OSC"""
    else:
        return "Error: OSC client not initialized. Install python-osc: uv add python-osc"


@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """
    Set the project tempo in BPM.
    
    Args:
        tempo: Tempo in beats per minute (20-999)
    """
    if tempo < 20 or tempo > 999:
        return "Error: Tempo must be between 20 and 999 BPM"
    
    bridge = get_bridge()
    if bridge.set_tempo(tempo):
        return f"Tempo set to {tempo} BPM"
    return "Error: Failed to send OSC command"


# =============================================================================
# TRANSPORT TOOLS
# =============================================================================

@mcp.tool()
def play(ctx: Context) -> str:
    """Start playback."""
    bridge = get_bridge()
    if bridge.play():
        return "Playback started"
    return "Error: OSC command failed"


@mcp.tool()
def stop(ctx: Context) -> str:
    """Stop playback."""
    bridge = get_bridge()
    if bridge.stop():
        return "Playback stopped"
    return "Error: OSC command failed"


@mcp.tool()
def record(ctx: Context) -> str:
    """Start recording."""
    bridge = get_bridge()
    if bridge.record():
        return "Recording started"
    return "Error: OSC command failed"


@mcp.tool()
def goto_position(ctx: Context, seconds: float) -> str:
    """
    Move cursor to a specific position.
    
    Args:
        seconds: Position in seconds
    """
    bridge = get_bridge()
    if bridge.goto_position(seconds):
        return f"Cursor moved to {seconds}s"
    return "Error: OSC command failed"


# =============================================================================
# TRACK TOOLS
# =============================================================================

@mcp.tool()
def create_track(ctx: Context, name: str = "New Track") -> str:
    """
    Create a new track.
    
    Args:
        name: Name for the new track
    """
    bridge = get_bridge()
    result = bridge.create_track(name)
    return result.get("message", "Track created")


@mcp.tool()
def set_track_volume(ctx: Context, track_number: int, volume: float) -> str:
    """
    Set track volume.
    
    Args:
        track_number: Track number (1-based, as shown in REAPER)
        volume: Volume level (0.0 = -inf dB, 1.0 = 0 dB)
    """
    bridge = get_bridge()
    # Convert to 0-indexed internally
    if bridge.set_track_volume(track_number - 1, max(0.0, min(1.0, volume))):
        return f"Track {track_number} volume set to {volume}"
    return "Error: OSC command failed"


@mcp.tool()
def set_track_pan(ctx: Context, track_number: int, pan: float) -> str:
    """
    Set track pan position.
    
    Args:
        track_number: Track number (1-based)
        pan: Pan position (-1.0 = full left, 0.0 = center, 1.0 = full right)
    """
    bridge = get_bridge()
    if bridge.set_track_pan(track_number - 1, max(-1.0, min(1.0, pan))):
        return f"Track {track_number} pan set to {pan}"
    return "Error: OSC command failed"


@mcp.tool()
def mute_track(ctx: Context, track_number: int, muted: bool = True) -> str:
    """
    Mute or unmute a track.
    
    Args:
        track_number: Track number (1-based)
        muted: True to mute, False to unmute
    """
    bridge = get_bridge()
    if bridge.set_track_mute(track_number - 1, muted):
        state = "muted" if muted else "unmuted"
        return f"Track {track_number} {state}"
    return "Error: OSC command failed"


@mcp.tool()
def solo_track(ctx: Context, track_number: int, solo: bool = True) -> str:
    """
    Solo or unsolo a track.
    
    Args:
        track_number: Track number (1-based)
        solo: True to solo, False to unsolo
    """
    bridge = get_bridge()
    if bridge.set_track_solo(track_number - 1, solo):
        state = "soloed" if solo else "unsoloed"
        return f"Track {track_number} {state}"
    return "Error: OSC command failed"


@mcp.tool()
def arm_track(ctx: Context, track_number: int, armed: bool = True) -> str:
    """
    Arm or disarm a track for recording.
    
    Args:
        track_number: Track number (1-based)
        armed: True to arm, False to disarm
    """
    bridge = get_bridge()
    if bridge.set_track_arm(track_number - 1, armed):
        state = "armed" if armed else "disarmed"
        return f"Track {track_number} {state}"
    return "Error: OSC command failed"


@mcp.tool()
def select_track(ctx: Context, track_number: int) -> str:
    """
    Select a track.
    
    Args:
        track_number: Track number (1-based)
    """
    bridge = get_bridge()
    if bridge.select_track(track_number - 1):
        return f"Track {track_number} selected"
    return "Error: OSC command failed"


# =============================================================================
# MIDI TOOLS (File-based)
# =============================================================================

@mcp.tool()
def create_midi_item(
    ctx: Context,
    track_number: int,
    position: float = 0.0,
    length: float = 4.0
) -> str:
    """
    Create a MIDI item on a track.
    
    Args:
        track_number: Track number (1-based)
        position: Start position in beats
        length: Length in beats (default: 4 = 1 bar in 4/4)
    """
    bridge = get_bridge()
    result = bridge.insert_midi_item(track_number - 1, position, length)
    return result.get("message", "MIDI item created")


@mcp.tool()
def add_notes(
    ctx: Context,
    track_number: int,
    item_index: int,
    notes: List[Dict[str, Any]]
) -> str:
    """
    Add MIDI notes to an existing MIDI item.
    
    Args:
        track_number: Track number (1-based)
        item_index: Index of the MIDI item (0-based)
        notes: List of note dictionaries with:
            - pitch: MIDI note number (0-127, middle C = 60)
            - start: Start position in beats (relative to item)
            - duration: Duration in beats
            - velocity: Velocity (1-127, default 100)
    """
    bridge = get_bridge()
    result = bridge.add_notes(track_number - 1, item_index, notes)
    return result.get("message", f"Added {len(notes)} note(s)")


@mcp.tool()
def execute_lua(ctx: Context, code: str) -> str:
    """
    Execute arbitrary Lua code in REAPER.
    
    This gives full control over REAPER via ReaScript.
    The code runs in REAPER's Lua environment with access to the reaper.* API.
    
    Args:
        code: Lua code to execute
    
    Example:
        execute_lua("reaper.ShowMessageBox('Hello from MCP!', 'Test', 0)")
    """
    bridge = get_bridge()
    result = bridge.execute_lua(code)
    return result.get("message", "Lua code executed")


# =============================================================================
# ACTION TOOLS
# =============================================================================

@mcp.tool()
def trigger_action(ctx: Context, action_name: str) -> str:
    """
    Trigger a REAPER action by name.
    
    Available actions:
    - Transport: play, stop, pause, record, rewind, forward
    - Project: save, save_as, new_project, undo, redo
    - Tracks: insert_track, delete_track, duplicate_track
    - View: zoom_fit, toggle_mixer
    
    Args:
        action_name: Name of the action to trigger
    """
    bridge = get_bridge()
    if bridge.trigger_action_by_name(action_name):
        return f"Triggered action: {action_name}"
    return f"Error: Unknown action '{action_name}'"


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Run the MCP server."""
    logger.info("Starting Scythe MCP Server (OSC mode)...")
    mcp.run()


if __name__ == "__main__":
    main()

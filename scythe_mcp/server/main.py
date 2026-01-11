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
# GENERATOR TOOLS
# =============================================================================

from ..generators.drums import generate_drum_pattern
from ..generators.basslines import generate_bassline
from ..generators.melodies import generate_melody
from ..music_theory.chords import parse_chord
from ..music_theory.scales import Scale

@mcp.tool()
def add_drum_track(
    ctx: Context,
    genre: str = "electronic",
    bars: int = 4,
    variation: str = "basic"
) -> str:
    """
    Generate and add a drum track.
    
    Args:
        genre: Genre (electronic, hiphop, rock, trap, lofi)
        bars: Number of bars
        variation: Pattern variation
    """
    bridge = get_bridge()
    
    # Create track
    track_name = f"{genre.capitalize()} Drums"
    res = bridge.create_track(track_name)
    # Give it a moment to exist in REAPER logic (approx)
    import time
    time.sleep(0.3)
    
    if not res.get("success") or "track_index" not in res:
         return f"Error: Failed to create track. {res.get('message')}"
    
    track_index = res["track_index"]

    # Generate patterns
    pattern = generate_drum_pattern(genre=genre, bars=bars, variation=variation)
    notes = pattern.to_midi_notes()

    # Insert MIDI item
    bridge.insert_midi_item(track_index, position=0, length=bars * 4) # Assuming 4/4
    
    # Add Notes
    # bridge.add_notes now handles logic internally via execute_lua
    bridge.add_notes(track_index, 0, notes) # item_index 0 (newest/first)
    
    return f"Created drum track '{track_name}' ID:{track_index+1} with {len(notes)} notes."

# Forgetting complexities, let's just expose the RAW generators which return JSON,
# and let the user (or LLM) use `create_midi_item` + `add_notes` manually?
# NO, the user wants "tools" to do it.
# Let's implement robust Logic in the tool.

@mcp.tool()
def add_bass_track(
    ctx: Context,
    progression: List[str],
    style: str = "root_fifth",
    bars_per_chord: int = 4
) -> str:
    """
    Generate and add a bass track provided a chord progression.
    
    Args:
        progression: List of chords ["Cm7", "Fm7"]
        style: Bass style (root, root_fifth, walking, synth, 808)
    """
    bridge = get_bridge()
    track_name = f"Bass ({style})"
    res = bridge.create_track(track_name)
    import time
    time.sleep(0.3)
    
    if not res.get("success") or "track_index" not in res:
         return f"Error: Failed to create track. {res.get('message')}"
    track_index = res["track_index"]
    
    chords = [parse_chord(name) for name in progression]
    bass = generate_bassline(chords, style=style, beats_per_chord=float(bars_per_chord))
    notes = bass.to_dict_list()
    
    bridge.insert_midi_item(track_index, 0, len(chords) * bars_per_chord)
    bridge.add_notes(track_index, 0, notes)
    
    return f"Created bass track with {len(notes)} notes."

@mcp.tool()
def add_melody_track(
    ctx: Context,
    key: str = "C",
    scale_type: str = "minor",
    style: str = "varied",
    bars: int = 4
) -> str:
    """
    Generate and add a melody track.
    
    Args:
        key: Key (C, D#, etc)
        scale_type: major, minor, dorian, etc.
        style: varied, straight, syncopated
    """
    bridge = get_bridge()
    track_name = f"Melody ({key} {scale_type})"
    res = bridge.create_track(track_name)
    import time
    time.sleep(0.3)
    
    if not res.get("success") or "track_index" not in res:
         return f"Error: Failed to create track. {res.get('message')}"
    track_index = res["track_index"]
    
    scale = Scale(key, scale_type)
    melody = generate_melody(scale=scale, style=style, bars=bars)
    notes = melody.to_dict_list()
    
    bridge.insert_midi_item(track_index, 0, bars * 4)
    bridge.add_notes(track_index, 0, notes)
    
    return f"Created melody track with {len(notes)} notes."

@mcp.tool()
def create_song_sketch(
    ctx: Context,
    genre: str = "electronic",
    key: str = "C",
    scale_type: str = "minor",
    bars: int = 4,
    tempo: int = 120
) -> str:
    """
    Generate a full song sketch (Drums, Bass, Harmony, Melody).
    
    Args:
        genre: Musical genre (electronic, trap, lo-fi, etc)
        key: Root key
        scale_type: Scale type (major, minor)
        bars: Length in bars
        tempo: Project tempo
    """
    bridge = get_bridge()
    bridge.set_tempo(tempo)
    
    # 1. Progression
    from ..music_theory.progressions import get_progression
    # Map scale_type to mode (major/minor)
    mode = "minor" if "minor" in scale_type else "major"
    prog_obj = get_progression(key=key, genre=genre, mode=mode)
    prog_chords = prog_obj.to_chords()
    prog_names = [f"{c.root}{c.chord_type}" for c in prog_chords] # Construct chord names manually or use str(c) if available
    
    results = []
    
    # 2. Drums
    results.append(add_drum_track(ctx, genre=genre, bars=bars))
    
    # 3. Bass
    # Map genre to bass style
    bass_style = "root_fifth"
    if genre in ["trap", "hiphop"]: bass_style = "808"
    elif genre == "electronic": bass_style = "synth"
    
    results.append(add_bass_track(ctx, progression=prog_names, style=bass_style, bars_per_chord=1)) # Prog usually 1 chord/bar?
    # generate_progression returns list of Chords. Length=bars implies 1 chord per bar.
    
    # 4. Melody
    results.append(add_melody_track(ctx, key=key, scale_type=scale_type, style="syncopated", bars=bars))
    
    return "Song Sketch Created:\n- " + "\n- ".join(results)

@mcp.tool()
def generate_drums_json(
    ctx: Context,
    genre: str = "electronic",
    bars: int = 4
) -> str:
    """
    Generate drum pattern data (JSON) to be used with add_notes.
    Returns the note list directly.
    """
    pattern = generate_drum_pattern(genre=genre, bars=bars)
    import json
    return json.dumps(pattern.to_midi_notes())

@mcp.tool()
def generate_bass_json(
    ctx: Context,
    progression: List[str],
    style: str = "root_fifth",
    bars_per_chord: int = 4
) -> str:
    """
    Generate bassline data (JSON) from chord progression.
    
    Args:
        progression: List of chord names ["Cmaj7", "Am7"]
        style: Bass style
    """
    chords = [parse_chord(name) for name in progression]
    bass = generate_bassline(chords, style=style, beats_per_chord=float(bars_per_chord))
    import json
    return json.dumps(bass.to_dict_list())

@mcp.tool()
def generate_melody_json(
    ctx: Context,
    key: str = "C",
    scale_type: str = "minor",
    style: str = "varied"
) -> str:
    """
    Generate melody data (JSON).
    """
    scale = Scale(key, scale_type)
    melody = generate_melody(scale=scale, style=style)
    import json
    return json.dumps(melody.to_dict_list())
    
# ENTRY POINT

def main():
    """Run the MCP server."""
    logger.info("Starting Scythe MCP Server (OSC mode)...")
    mcp.run()


if __name__ == "__main__":
    main()

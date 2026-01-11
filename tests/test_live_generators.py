import time
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scythe_mcp.server.reaper_bridge import get_bridge
from scythe_mcp.generators.drums import generate_drum_pattern
from scythe_mcp.generators.basslines import generate_bassline
from scythe_mcp.generators.melodies import generate_melody
from scythe_mcp.music_theory.chords import parse_chord
from scythe_mcp.music_theory.scales import Scale

def main():
    print("Connecting to REAPER...")
    bridge = get_bridge()
    
    # 1. Transport reset
    bridge.stop()
    bridge.goto_position(0)
    
    # 2. DRUMS
    print("\n--- Generating Drums (HipHop) ---")
    drum_track_name = "MCP Drums"
    bridge.create_track(drum_track_name)
    # Give REAPER a moment to process the new track
    time.sleep(0.5)
    
    # We assume the new track is the last one
    # Note: In a robust app we'd track IDs, but for now we assume sequentially added.
    # If the project was empty, this is Track 1.
    
    # Let's clean up project first? No, let's just append.
    # Note: track_index is 0-based
    
    # Since we can't easily query track count via OSC/file without a complex feedback loop,
    # we'll assume the user has a fresh empty project or we are appending.
    # Ideally, we should count tracks first.
    # bridge.execute_lua("return reaper.CountTracks(0)") ... but that requires async polling.
    
    # For this test, let's assume we just created track 1, 2, 3.
    # Track 1: Drums
    
    drums = generate_drum_pattern(genre="hiphop", bars=4)
    # Flatten drum tracks
    drum_notes = drums.to_midi_notes()
    
    bridge.insert_midi_item(0, position=0, length=4*4) # 4 bars
    time.sleep(0.2)
    bridge.add_notes(0, 0, drum_notes)
    
    # 3. BASS
    print("\n--- Generating Bass (Synth) ---")
    bridge.create_track("MCP Bass")
    time.sleep(0.5)
    
    # Simple progression: Cm7 - Fm7 - Gm7 - Cm7
    chords = [
        parse_chord("Cm7"),
        parse_chord("Fm7"),
        parse_chord("Gm7"),
        parse_chord("Cm7")
    ]
    
    bass = generate_bassline(
        chords=chords,
        style="synth",
        beats_per_chord=4.0
    )
    bass_notes = bass.to_dict_list()
    
    bridge.insert_midi_item(1, position=0, length=4*4)
    time.sleep(0.2)
    bridge.add_notes(1, 0, bass_notes)
    
    # 4. MELODY
    print("\n--- Generating Melody (C Minor) ---")
    bridge.create_track("MCP Melody")
    time.sleep(0.5)
    
    scale = Scale("C", "minor", octave=5)
    melody = generate_melody(
        scale=scale,
        bars=4,
        style="syncopated",
        density=0.6
    )
    melody_notes = melody.to_dict_list()
    
    bridge.insert_midi_item(2, position=0, length=4*4)
    time.sleep(0.2)
    bridge.add_notes(2, 0, melody_notes)
    
    print("\nDone! Check REAPER.")
    print(f"Generated {len(drum_notes)} drum hits")
    print(f"Generated {len(bass_notes)} bass notes")
    print(f"Generated {len(melody_notes)} melody notes")

if __name__ == "__main__":
    main()

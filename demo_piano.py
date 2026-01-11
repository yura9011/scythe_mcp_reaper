from scythe_mcp.server.reaper_bridge import ReaperBridge
from scythe_mcp.music_theory.progressions import get_progression
from scythe_mcp.music_theory.chords import parse_chord
from scythe_mcp.music_theory.scales import note_to_midi
import time
import random

def demo_piano():
    bridge = ReaperBridge()
    
    print("1. Clearing Project...")
    # 40296 = Track: Select all tracks
    bridge.trigger_action(40296)
    # 40005 = Track: Remove tracks
    bridge.trigger_action(40005)
    
    # 40042 = Transport: Go to start of project
    bridge.trigger_action(40042)
    time.sleep(1.0)
    
    # Set Tempo
    print("2. Setting Slow Tempo (68 BPM)...")
    bridge.set_tempo(68)
    
    # Create Track
    print("3. Creating Piano Track...")
    res = bridge.create_track("Solo Piano")
    if not res.get("success"):
        print(f"Error creating track: {res}")
        return
    track_idx = res["track_index"]
    print(f"Created Track Index: {track_idx}")
    time.sleep(0.5)
    
    # --- MUSIC GENERATION ---
    print("4. Generating Music (Chord-Based Melody)...")
    
    # Get a simple progression in C minor
    prog_obj = get_progression("C", "pop", style="sensitive", mode="minor")
    base_chords = prog_obj.to_chords(octave=3)
    
    if not base_chords:
         base_chords = [parse_chord(n) for n in ["Cm", "Ab", "Eb", "Bb"]]
    
    # Repeat progression 4 times for length
    progression_chords = base_chords * 4
    
    all_notes = []
    current_beat = 0
    beats_per_chord = 4  # Each chord lasts one bar (4 beats)
    
    for i, chord in enumerate(progression_chords):
        root_midi = note_to_midi(chord.root, 3)  # Octave 3 for left hand
        
        # === LEFT HAND: Simple root + fifth (or root only) ===
        # Play root on beat 1
        all_notes.append({
            "pitch": root_midi - 12,  # Deep bass (octave 2)
            "start": current_beat,
            "duration": 3.8,  # Almost full bar
            "velocity": 80
        })
        # Play root again in octave 3
        all_notes.append({
            "pitch": root_midi,
            "start": current_beat,
            "duration": 3.8,
            "velocity": 70
        })
        
        # === RIGHT HAND: Chord tones as melody ===
        # Get the actual notes of the chord (root + intervals)
        chord_notes = [root_midi + interval for interval in chord.intervals]
        # Transpose up one octave for melody register
        melody_notes = [n + 12 for n in chord_notes]  # Now in octave 4
        
        # Play chord tones slowly: pick 2-3 notes
        # Beat 1: Root (octave 4)
        # Beat 3: Third or Fifth
        all_notes.append({
            "pitch": melody_notes[0],  # Root
            "start": current_beat,
            "duration": 1.9,  # Half note
            "velocity": 90
        })
        
        if len(melody_notes) >= 2:
            # Beat 3: Play the third (usually index 1)
            all_notes.append({
                "pitch": melody_notes[1],  # Third
                "start": current_beat + 2,
                "duration": 1.9,
                "velocity": 85
            })
        
        # Optional: every 2 bars, add a passing tone on beat 4 to connect
        if i % 2 == 1 and i < len(progression_chords) - 1:
            next_chord = progression_chords[i + 1]
            next_root = note_to_midi(next_chord.root, 4)
            # Passing tone: halfway between current root and next root
            current_melody_root = melody_notes[0]
            if next_root != current_melody_root:
                # Simple approach: go one step toward next root
                direction = 1 if next_root > current_melody_root else -1
                passing_note = current_melody_root + direction
                all_notes.append({
                    "pitch": passing_note,
                    "start": current_beat + 3.5,
                    "duration": 0.4,
                    "velocity": 65
                })
        
        current_beat += beats_per_chord
    
    # --- SEND TO REAPER ---
    print(f"5. Inserting {len(all_notes)} notes...")
    
    # Insert MIDI Item
    total_bars = len(progression_chords)
    res_item = bridge.insert_midi_item(track_idx, 0, total_bars * 4)
    print(f"Item Result: {res_item}")
    
    # Insert Notes
    res_notes = bridge.add_notes(track_idx, 0, all_notes)
    print(f"Result: {res_notes}")
    
    print("\nDONE! Press Play in REAPER.")
    print(f"Generated {len(progression_chords)} bars of slow piano in C minor.")

if __name__ == "__main__":
    demo_piano()

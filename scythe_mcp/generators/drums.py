"""
Scythe MCP - Drum Pattern Generator

Genre-specific drum patterns for electronic, hip-hop, rock, and more.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import random

from ..music_theory.rhythm import Note, Rhythm


# Standard GM drum map (MIDI notes)
DRUM_MAP = {
    "kick": 36,
    "snare": 38,
    "clap": 39,
    "closed_hat": 42,
    "open_hat": 46,
    "low_tom": 45,
    "mid_tom": 47,
    "high_tom": 50,
    "crash": 49,
    "ride": 51,
    "rimshot": 37,
    "cowbell": 56,
    "tambourine": 54,
    "shaker": 70,
}

# 808-style drum map (common in hip-hop/trap)
DRUM_MAP_808 = {
    "kick": 36,
    "snare": 38,
    "clap": 39,
    "closed_hat": 42,
    "open_hat": 46,
    "perc1": 75,
    "perc2": 67,
}


@dataclass
class DrumPattern:
    """A complete drum pattern with multiple instruments."""
    
    name: str
    bars: int
    bpm: float
    time_signature: tuple
    tracks: Dict[str, Rhythm]  # instrument -> rhythm
    
    def to_midi_notes(self, drum_map: Dict[str, int] = None) -> List[Dict]:
        """Convert all tracks to MIDI note list."""
        if drum_map is None:
            drum_map = DRUM_MAP
        
        all_notes = []
        for instrument, rhythm in self.tracks.items():
            pitch = drum_map.get(instrument, 36)
            for note in rhythm.notes:
                all_notes.append({
                    "pitch": pitch,
                    "start": note.start,
                    "duration": note.duration,
                    "velocity": note.velocity
                })
        
        # Sort by start time
        all_notes.sort(key=lambda n: n["start"])
        return all_notes


# =============================================================================
# GENRE PATTERNS
# =============================================================================

def _create_four_on_floor(bars: int = 4, velocity: int = 100) -> Rhythm:
    """Classic house/techno kick pattern."""
    notes = []
    for bar in range(bars):
        for beat in range(4):
            notes.append(Note(
                start=bar * 4 + beat,
                duration=0.25,
                velocity=velocity,
                pitch=DRUM_MAP["kick"]
            ))
    return Rhythm((4, 4), notes, bars * 4)


def _create_boom_bap_kick(bars: int = 4, velocity: int = 100) -> Rhythm:
    """Hip-hop boom bap kick pattern."""
    patterns = [
        [0.0, 1.75, 3.0],           # Classic
        [0.0, 0.75, 2.75],          # Variation 1
        [0.0, 1.5, 2.5, 3.5],       # Variation 2
    ]
    pattern = random.choice(patterns)
    
    notes = []
    for bar in range(bars):
        for pos in pattern:
            notes.append(Note(
                start=bar * 4 + pos,
                duration=0.25,
                velocity=velocity + random.randint(-5, 5),
                pitch=DRUM_MAP["kick"]
            ))
    return Rhythm((4, 4), notes, bars * 4)


def _create_trap_hihat(bars: int = 4, velocity: int = 80) -> Rhythm:
    """Trap-style hihat with rolls."""
    notes = []
    
    for bar in range(bars):
        for beat in range(4):
            # Regular eighth notes
            for eighth in range(2):
                pos = bar * 4 + beat + (eighth * 0.5)
                notes.append(Note(
                    start=pos,
                    duration=0.125,
                    velocity=velocity - (eighth * 10),
                    pitch=DRUM_MAP["closed_hat"]
                ))
            
            # Occasional triplet rolls
            if random.random() < 0.25:
                for triplet in range(3):
                    pos = bar * 4 + beat + (triplet / 6) + 0.5
                    notes.append(Note(
                        start=pos,
                        duration=0.08,
                        velocity=velocity - 20,
                        pitch=DRUM_MAP["closed_hat"]
                    ))
    
    return Rhythm((4, 4), notes, bars * 4)


def _create_backbeat_snare(bars: int = 4, velocity: int = 100) -> Rhythm:
    """Standard backbeat snare on 2 and 4."""
    notes = []
    for bar in range(bars):
        for beat in [1, 3]:  # 2 and 4 (0-indexed)
            notes.append(Note(
                start=bar * 4 + beat,
                duration=0.25,
                velocity=velocity,
                pitch=DRUM_MAP["snare"]
            ))
    return Rhythm((4, 4), notes, bars * 4)


def _create_offbeat_hat(bars: int = 4, velocity: int = 70) -> Rhythm:
    """Offbeat hi-hat pattern (disco/house)."""
    notes = []
    for bar in range(bars):
        for beat in range(4):
            notes.append(Note(
                start=bar * 4 + beat + 0.5,
                duration=0.25,
                velocity=velocity,
                pitch=DRUM_MAP["open_hat"]
            ))
    return Rhythm((4, 4), notes, bars * 4)


def _create_eighth_hat(bars: int = 4, velocity: int = 65) -> Rhythm:
    """Straight eighth note hi-hats."""
    notes = []
    for bar in range(bars):
        for beat in range(4):
            for eighth in range(2):
                notes.append(Note(
                    start=bar * 4 + beat + (eighth * 0.5),
                    duration=0.2,
                    velocity=velocity if eighth == 0 else velocity - 15,
                    pitch=DRUM_MAP["closed_hat"]
                ))
    return Rhythm((4, 4), notes, bars * 4)


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_drum_pattern(
    genre: str = "electronic",
    bars: int = 4,
    bpm: float = 120,
    variation: str = "basic",
    swing: float = 0.0
) -> DrumPattern:
    """
    Generate a drum pattern for a specific genre.
    
    Args:
        genre: Genre (electronic, hiphop, rock, lofi, trap, etc.)
        bars: Number of bars
        bpm: Tempo
        variation: Pattern variation (basic, complex, minimal, etc.)
        swing: Swing amount (0.0 to 0.5)
    
    Returns:
        DrumPattern with all instrument tracks
    """
    tracks = {}
    
    genre = genre.lower()
    
    if genre in ("electronic", "house", "techno"):
        tracks["kick"] = _create_four_on_floor(bars)
        tracks["snare"] = _create_backbeat_snare(bars, 90)
        tracks["closed_hat"] = _create_eighth_hat(bars)
        tracks["open_hat"] = _create_offbeat_hat(bars)
        
    elif genre in ("hiphop", "hip-hop", "boom_bap", "lofi"):
        tracks["kick"] = _create_boom_bap_kick(bars)
        tracks["snare"] = _create_backbeat_snare(bars)
        tracks["closed_hat"] = _create_eighth_hat(bars, 55)
        swing = max(swing, 0.15)  # Lo-fi needs swing
        
    elif genre == "trap":
        tracks["kick"] = _create_boom_bap_kick(bars)
        tracks["snare"] = _create_backbeat_snare(bars, 110)
        tracks["closed_hat"] = _create_trap_hihat(bars)
        
    elif genre in ("rock", "punk", "emo"):
        tracks["kick"] = _create_four_on_floor(bars, 110)
        tracks["snare"] = _create_backbeat_snare(bars, 120)
        tracks["closed_hat"] = _create_eighth_hat(bars, 75)
        
    elif genre in ("chiptune", "8bit"):
        # Simple, punchy patterns
        tracks["kick"] = _create_four_on_floor(bars, 120)
        tracks["snare"] = _create_backbeat_snare(bars, 110)
        
    else:
        # Default pattern
        tracks["kick"] = _create_four_on_floor(bars)
        tracks["snare"] = _create_backbeat_snare(bars)
        tracks["closed_hat"] = _create_eighth_hat(bars)
    
    # Apply swing if specified
    if swing > 0:
        for name, rhythm in tracks.items():
            tracks[name] = rhythm.with_swing(swing)
    
    return DrumPattern(
        name=f"{genre}_{variation}",
        bars=bars,
        bpm=bpm,
        time_signature=(4, 4),
        tracks=tracks
    )

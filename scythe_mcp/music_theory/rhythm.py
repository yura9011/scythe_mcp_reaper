"""
Scythe MCP - Rhythm

Time signatures, swing, syncopation, and rhythmic patterns.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random


# Common time signatures as (numerator, denominator)
TIME_SIGNATURES: Dict[str, Tuple[int, int]] = {
    "4/4": (4, 4),
    "3/4": (3, 4),
    "2/4": (2, 4),
    "6/8": (6, 8),
    "12/8": (12, 8),
    "5/4": (5, 4),
    "7/4": (7, 4),
    "7/8": (7, 8),
    "9/8": (9, 8),
    "11/8": (11, 8),
}


@dataclass
class Note:
    """Represents a single note or hit."""
    
    start: float      # Position in beats
    duration: float   # Duration in beats
    velocity: int = 100
    pitch: int = 60   # MIDI note number
    
    def with_swing(self, amount: float = 0.33) -> "Note":
        """Apply swing to off-beat notes."""
        # Swing affects notes on the "and" of the beat
        beat_pos = self.start % 1.0
        
        if 0.4 < beat_pos < 0.6:  # Roughly on the off-beat
            new_start = self.start + (amount * 0.5)
            return Note(new_start, self.duration, self.velocity, self.pitch)
        
        return self
    
    def humanize(self, timing_range: float = 0.02, velocity_range: int = 10) -> "Note":
        """Add human-like variation."""
        timing_offset = random.uniform(-timing_range, timing_range)
        velocity_offset = random.randint(-velocity_range, velocity_range)
        
        return Note(
            start=max(0, self.start + timing_offset),
            duration=self.duration,
            velocity=max(1, min(127, self.velocity + velocity_offset)),
            pitch=self.pitch
        )


@dataclass
class Rhythm:
    """Represents a rhythmic pattern."""
    
    time_signature: Tuple[int, int]
    notes: List[Note]
    length_beats: float = 4.0
    
    @property
    def beats_per_bar(self) -> float:
        """Get beats per bar for this time signature."""
        num, denom = self.time_signature
        return num * (4.0 / denom)
    
    def to_dict_list(self) -> List[Dict]:
        """Convert to list of dictionaries for MCP transport."""
        return [
            {
                "start": n.start,
                "duration": n.duration,
                "velocity": n.velocity,
                "pitch": n.pitch
            }
            for n in self.notes
        ]
    
    def with_swing(self, amount: float = 0.33) -> "Rhythm":
        """Apply swing to the pattern."""
        return Rhythm(
            time_signature=self.time_signature,
            notes=[n.with_swing(amount) for n in self.notes],
            length_beats=self.length_beats
        )
    
    def humanize(self) -> "Rhythm":
        """Add human-like variation."""
        return Rhythm(
            time_signature=self.time_signature,
            notes=[n.humanize() for n in self.notes],
            length_beats=self.length_beats
        )
    
    def transpose(self, semitones: int) -> "Rhythm":
        """Transpose all notes by semitones."""
        return Rhythm(
            time_signature=self.time_signature,
            notes=[
                Note(n.start, n.duration, n.velocity, n.pitch + semitones)
                for n in self.notes
            ],
            length_beats=self.length_beats
        )
    
    def repeat(self, times: int) -> "Rhythm":
        """Repeat the pattern multiple times."""
        new_notes = []
        for i in range(times):
            offset = i * self.length_beats
            for note in self.notes:
                new_notes.append(Note(
                    start=note.start + offset,
                    duration=note.duration,
                    velocity=note.velocity,
                    pitch=note.pitch
                ))
        
        return Rhythm(
            time_signature=self.time_signature,
            notes=new_notes,
            length_beats=self.length_beats * times
        )


# Basic rhythmic subdivisions (positions within one beat)
SUBDIVISIONS = {
    "quarter": [0.0],
    "eighth": [0.0, 0.5],
    "triplet": [0.0, 1/3, 2/3],
    "sixteenth": [0.0, 0.25, 0.5, 0.75],
    "sextuplet": [0.0, 1/6, 2/6, 3/6, 4/6, 5/6],
}


def create_straight_pattern(
    beats: int = 4,
    subdivision: str = "quarter",
    pitch: int = 60,
    velocity: int = 100,
    accent_pattern: Optional[List[int]] = None
) -> Rhythm:
    """Create a straight rhythmic pattern."""
    divisions = SUBDIVISIONS.get(subdivision, [0.0])
    notes = []
    
    for beat in range(beats):
        for i, div in enumerate(divisions):
            vel = velocity
            if accent_pattern:
                accent_idx = (beat * len(divisions) + i) % len(accent_pattern)
                vel = int(velocity * (1.3 if accent_pattern[accent_idx] else 0.7))
            
            notes.append(Note(
                start=beat + div,
                duration=1.0 / len(divisions) * 0.9,
                velocity=vel,
                pitch=pitch
            ))
    
    return Rhythm(
        time_signature=(4, 4),
        notes=notes,
        length_beats=beats
    )


def create_syncopated_pattern(
    beats: int = 4,
    density: float = 0.5,
    pitch: int = 60,
    velocity: int = 100
) -> Rhythm:
    """Create a syncopated pattern with off-beat emphasis."""
    notes = []
    
    # 16th note grid
    for beat in range(beats):
        for sixteenth in range(4):
            pos = beat + (sixteenth * 0.25)
            
            # Favor off-beats based on density
            is_on_beat = sixteenth == 0
            threshold = 0.3 if is_on_beat else density
            
            if random.random() < threshold:
                notes.append(Note(
                    start=pos,
                    duration=0.2,
                    velocity=velocity if is_on_beat else int(velocity * 0.8),
                    pitch=pitch
                ))
    
    return Rhythm(
        time_signature=(4, 4),
        notes=notes,
        length_beats=beats
    )


# Common rhythmic patterns
COMMON_RHYTHMS = {
    "four_on_floor": [0.0, 1.0, 2.0, 3.0],  # House/techno kick
    "backbeat": [1.0, 3.0],                   # Rock/pop snare
    "boom_bap": [0.0, 1.5, 2.75],             # Hip-hop kick
    "reggae_one_drop": [2.5],                 # Reggae
    "disco": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],  # Disco hi-hat
}


def get_common_rhythm(
    name: str,
    bars: int = 1,
    pitch: int = 60,
    velocity: int = 100
) -> Rhythm:
    """Get a common rhythmic pattern."""
    pattern = COMMON_RHYTHMS.get(name, COMMON_RHYTHMS["four_on_floor"])
    notes = []
    
    for bar in range(bars):
        offset = bar * 4.0
        for pos in pattern:
            notes.append(Note(
                start=pos + offset,
                duration=0.25,
                velocity=velocity,
                pitch=pitch
            ))
    
    return Rhythm(
        time_signature=(4, 4),
        notes=notes,
        length_beats=4.0 * bars
    )

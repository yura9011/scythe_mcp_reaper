"""
Scythe MCP - Bassline Generator

Generate basslines from chord progressions with genre-specific styles.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import random

from ..music_theory.scales import Scale
from ..music_theory.chords import Chord
from ..music_theory.rhythm import Note, Rhythm


@dataclass 
class Bassline:
    """A generated bassline."""
    
    notes: List[Note]
    length_beats: float
    style: str
    
    def to_dict_list(self) -> List[Dict]:
        """Convert to list of dicts for MCP transport."""
        return [
            {
                "pitch": n.pitch,
                "start": n.start,
                "duration": n.duration,
                "velocity": n.velocity
            }
            for n in self.notes
        ]


def _root_notes_only(
    chords: List[Chord],
    beats_per_chord: float = 4.0,
    octave_offset: int = -2
) -> List[Note]:
    """Simple root note bassline."""
    notes = []
    position = 0.0
    
    for chord in chords:
        root_midi = chord.root_midi + (octave_offset * 12)
        notes.append(Note(
            start=position,
            duration=beats_per_chord * 0.9,
            velocity=100,
            pitch=root_midi
        ))
        position += beats_per_chord
    
    return notes


def _root_fifth_pattern(
    chords: List[Chord],
    beats_per_chord: float = 4.0,
    octave_offset: int = -2
) -> List[Note]:
    """Root on 1, fifth on 3 pattern."""
    notes = []
    position = 0.0
    
    for chord in chords:
        root_midi = chord.root_midi + (octave_offset * 12)
        fifth_midi = root_midi + 7  # Perfect fifth
        
        # Root on beat 1
        notes.append(Note(
            start=position,
            duration=1.8,
            velocity=100,
            pitch=root_midi
        ))
        
        # Fifth on beat 3
        notes.append(Note(
            start=position + 2,
            duration=1.8,
            velocity=85,
            pitch=fifth_midi
        ))
        
        position += beats_per_chord
    
    return notes


def _walking_bass(
    chords: List[Chord],
    beats_per_chord: float = 4.0,
    octave_offset: int = -2
) -> List[Note]:
    """Jazz/blues walking bass pattern."""
    notes = []
    position = 0.0
    
    for i, chord in enumerate(chords):
        root_midi = chord.root_midi + (octave_offset * 12)
        chord_notes = [root_midi + interval for interval in chord.intervals]
        
        # Get target note (root of next chord)
        next_chord = chords[(i + 1) % len(chords)]
        target = next_chord.root_midi + (octave_offset * 12)
        
        # Walking pattern: root, chord tone, passing tone, approach
        pattern = [
            root_midi,
            random.choice(chord_notes),
            root_midi + random.choice([2, 3, 5]),
            target - 1 if random.random() < 0.5 else target + 1
        ]
        
        for beat, pitch in enumerate(pattern):
            notes.append(Note(
                start=position + beat,
                duration=0.9,
                velocity=100 if beat == 0 else 85,
                pitch=pitch
            ))
        
        position += beats_per_chord
    
    return notes


def _synth_bass(
    chords: List[Chord],
    beats_per_chord: float = 4.0,
    octave_offset: int = -2
) -> List[Note]:
    """Electronic synth bass with rhythmic variation."""
    notes = []
    position = 0.0
    
    patterns = [
        [0.0, 0.75, 1.5, 2.0, 3.0, 3.5],   # Driving
        [0.0, 1.0, 2.5, 3.0],               # Sparse
        [0.0, 0.5, 1.0, 2.0, 2.5, 3.0],     # 16th feel
    ]
    pattern = random.choice(patterns)
    
    for chord in chords:
        root_midi = chord.root_midi + (octave_offset * 12)
        
        for beat_offset in pattern:
            notes.append(Note(
                start=position + beat_offset,
                duration=0.4,
                velocity=100 if beat_offset == 0 else 80,
                pitch=root_midi
            ))
        
        position += beats_per_chord
    
    return notes


def _octave_bass(
    chords: List[Chord],
    beats_per_chord: float = 4.0,
    octave_offset: int = -2
) -> List[Note]:
    """Disco/funk octave bass pattern."""
    notes = []
    position = 0.0
    
    for chord in chords:
        root_midi = chord.root_midi + (octave_offset * 12)
        
        for beat in range(int(beats_per_chord)):
            # Low note
            notes.append(Note(
                start=position + beat,
                duration=0.2,
                velocity=100,
                pitch=root_midi
            ))
            # High octave
            notes.append(Note(
                start=position + beat + 0.5,
                duration=0.2,
                velocity=80,
                pitch=root_midi + 12
            ))
        
        position += beats_per_chord
    
    return notes


def _trap_808(
    chords: List[Chord],
    beats_per_chord: float = 4.0,
    octave_offset: int = -3  # Lower for 808
) -> List[Note]:
    """Trap 808 bass with slides."""
    notes = []
    position = 0.0
    
    for chord in chords:
        root_midi = chord.root_midi + (octave_offset * 12)
        
        # Long sustaining 808 hits
        patterns = [
            [(0.0, 3.0), (3.0, 0.9)],
            [(0.0, 1.5), (1.75, 2.0)],
            [(0.0, 4.0)],
        ]
        pattern = random.choice(patterns)
        
        for start, duration in pattern:
            notes.append(Note(
                start=position + start,
                duration=duration,
                velocity=110,
                pitch=root_midi
            ))
        
        position += beats_per_chord
    
    return notes


# Style mapping
BASS_STYLES = {
    "root": _root_notes_only,
    "root_fifth": _root_fifth_pattern,
    "walking": _walking_bass,
    "synth": _synth_bass,
    "octave": _octave_bass,
    "808": _trap_808,
}


def generate_bassline(
    chords: List[Chord],
    style: str = "root_fifth",
    beats_per_chord: float = 4.0,
    octave: int = 2
) -> Bassline:
    """
    Generate a bassline from a chord progression.
    
    Args:
        chords: List of Chord objects
        style: Bass style (root, root_fifth, walking, synth, octave, 808)
        beats_per_chord: Duration of each chord in beats
        octave: Bass octave (default 2)
    
    Returns:
        Bassline object with generated notes
    """
    # Adjust chord octaves
    adjusted_chords = [
        Chord(
            root=c.root,
            chord_type=c.chord_type,
            octave=octave
        )
        for c in chords
    ]
    
    generator = BASS_STYLES.get(style.lower(), _root_fifth_pattern)
    notes = generator(adjusted_chords, beats_per_chord, 0)
    
    return Bassline(
        notes=notes,
        length_beats=len(chords) * beats_per_chord,
        style=style
    )

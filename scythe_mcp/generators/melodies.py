"""
Scythe MCP - Melody Generator

Generate melodies based on scales, chords, and stylistic patterns.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random

from ..music_theory.scales import Scale
from ..music_theory.chords import Chord
from ..music_theory.rhythm import Note, Rhythm


@dataclass
class Melody:
    """A generated melody."""
    
    notes: List[Note]
    length_beats: float
    scale: Scale
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


def _generate_contour(
    length: int,
    style: str = "arch"
) -> List[int]:
    """
    Generate a melodic contour (relative direction hints).
    
    Returns list of direction values: -2 (down big), -1 (down), 0 (same), 1 (up), 2 (up big)
    """
    if style == "arch":
        # Rise then fall
        mid = length // 2
        contour = [1] * mid + [-1] * (length - mid)
    elif style == "descending":
        contour = [-1] * length
    elif style == "ascending":
        contour = [1] * length
    elif style == "wave":
        contour = []
        for i in range(length):
            phase = (i % 4)
            if phase < 2:
                contour.append(1)
            else:
                contour.append(-1)
    else:  # random
        contour = [random.choice([-1, 0, 0, 1]) for _ in range(length)]
    
    return contour


def _apply_contour_to_scale(
    scale: Scale,
    contour: List[int],
    start_degree: int = 1,
    octave_range: Tuple[int, int] = (-1, 1)
) -> List[int]:
    """Convert contour to actual MIDI notes using scale degrees."""
    notes = []
    current_degree = start_degree
    
    for direction in contour:
        # Move by scale degree
        step = direction
        if abs(direction) == 2:
            step = direction * random.randint(2, 3)  # Larger leap
        
        current_degree += step
        
        # Keep within range
        num_notes = len(scale.intervals)
        while current_degree > num_notes * (1 + octave_range[1]):
            current_degree -= num_notes
        while current_degree < 1 + (num_notes * octave_range[0]):
            current_degree += num_notes
        
        midi_note = scale.degree_to_midi(current_degree)
        notes.append(midi_note)
    
    return notes


def _generate_rhythm_pattern(
    beats: float,
    density: float = 0.5,
    style: str = "varied"
) -> List[Tuple[float, float]]:
    """
    Generate rhythm pattern as (start, duration) tuples.
    """
    positions = []
    
    if style == "straight":
        # Regular intervals
        note_length = 1.0 if density > 0.5 else 2.0
        pos = 0.0
        while pos < beats:
            dur = note_length * random.uniform(0.8, 1.0)
            positions.append((pos, dur))
            pos += note_length
            
    elif style == "syncopated":
        # Off-beat emphasis
        pos = 0.0
        while pos < beats:
            if random.random() < 0.3:
                pos += 0.5  # Offset start
            
            dur = random.choice([0.5, 0.75, 1.0, 1.5])
            if pos + dur <= beats:
                positions.append((pos, dur))
            
            pos += random.choice([0.5, 1.0, 1.5])
            
    else:  # varied
        pos = 0.0
        while pos < beats:
            dur = random.choice([0.25, 0.5, 0.75, 1.0, 1.5, 2.0])
            dur *= random.uniform(0.9, 1.0)  # Slight variation
            
            if pos + dur <= beats:
                positions.append((pos, dur))
            
            # Gap between notes
            gap = random.choice([0, 0, 0.25, 0.5]) if density > 0.5 else random.choice([0.25, 0.5, 1.0])
            pos += dur + gap
    
    return positions


def generate_melody(
    scale: Scale = None,
    key: str = "C",
    scale_type: str = "major",
    bars: int = 4,
    style: str = "varied",
    contour: str = "arch",
    density: float = 0.5,
    octave: int = 5
) -> Melody:
    """
    Generate a melody based on scale and style.
    
    Args:
        scale: Scale object (optional, will create from key/scale_type if not provided)
        key: Root note if scale not provided
        scale_type: Scale type if scale not provided
        bars: Number of bars
        style: Rhythmic style (straight, syncopated, varied)
        contour: Melodic shape (arch, ascending, descending, wave, random)
        density: Note density (0.0 sparse to 1.0 dense)
        octave: Melody octave
    
    Returns:
        Melody object with generated notes
    """
    if scale is None:
        scale = Scale(root=key, scale_type=scale_type, octave=octave)
    
    beats = bars * 4  # Assuming 4/4
    
    # Generate rhythm
    rhythm_pattern = _generate_rhythm_pattern(beats, density, style)
    
    if not rhythm_pattern:
        # Fallback to simple pattern
        rhythm_pattern = [(i * 1.0, 0.9) for i in range(bars * 4)]
    
    # Generate pitch contour
    pitch_contour = _generate_contour(len(rhythm_pattern), contour)
    
    # Convert to actual pitches
    pitches = _apply_contour_to_scale(
        scale,
        pitch_contour,
        start_degree=random.choice([1, 3, 5]),  # Start on chord tone
        octave_range=(-1, 1)
    )
    
    # Combine rhythm and pitch
    notes = []
    for (start, duration), pitch in zip(rhythm_pattern, pitches):
        velocity = random.randint(75, 100)
        
        # Accent downbeats
        if start % 1.0 == 0:
            velocity = min(127, velocity + 15)
        
        notes.append(Note(
            start=start,
            duration=duration,
            velocity=velocity,
            pitch=pitch
        ))
    
    return Melody(
        notes=notes,
        length_beats=beats,
        scale=scale,
        style=style
    )


def generate_arpeggio(
    chord: Chord,
    bars: int = 1,
    pattern: str = "up",
    note_length: float = 0.25,
    octaves: int = 1
) -> Melody:
    """
    Generate an arpeggio from a chord.
    
    Args:
        chord: Chord to arpeggiate
        bars: Number of bars
        pattern: Arpeggio pattern (up, down, up_down, random)
        note_length: Duration of each note
        octaves: Number of octaves to span
    
    Returns:
        Melody object with arpeggio notes
    """
    chord_notes = chord.get_notes()
    
    # Extend to multiple octaves
    all_notes = []
    for oct in range(octaves):
        for note in chord_notes:
            all_notes.append(note + (oct * 12))
    
    # Create pattern sequence
    if pattern == "up":
        sequence = all_notes
    elif pattern == "down":
        sequence = list(reversed(all_notes))
    elif pattern == "up_down":
        sequence = all_notes + list(reversed(all_notes[1:-1]))
    else:  # random
        sequence = all_notes.copy()
        random.shuffle(sequence)
    
    # Generate notes
    notes = []
    position = 0.0
    beats = bars * 4
    
    while position < beats:
        idx = int((position / note_length) % len(sequence))
        pitch = sequence[idx]
        
        notes.append(Note(
            start=position,
            duration=note_length * 0.9,
            velocity=85,
            pitch=pitch
        ))
        
        position += note_length
    
    return Melody(
        notes=notes,
        length_beats=beats,
        scale=Scale(chord.root, "major", chord.octave),
        style=f"arpeggio_{pattern}"
    )

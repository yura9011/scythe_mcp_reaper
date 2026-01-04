"""
Scythe MCP - Scales and Modes

Comprehensive scale definitions including major, minor, modes,
pentatonic, blues, and exotic scales.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass


# Note names and their MIDI offsets from C
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
ENHARMONIC = {
    'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#', 
    'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B',
    'E#': 'F', 'B#': 'C'
}


def note_to_midi(note: str, octave: int = 4) -> int:
    """Convert note name to MIDI number. Middle C (C4) = 60."""
    note_upper = note.upper()
    if note_upper in ENHARMONIC:
        note_upper = ENHARMONIC[note_upper]
    
    if note_upper not in NOTE_NAMES:
        raise ValueError(f"Unknown note: {note}")
    
    return NOTE_NAMES.index(note_upper) + (octave + 1) * 12


def midi_to_note(midi: int) -> Tuple[str, int]:
    """Convert MIDI number to note name and octave."""
    octave = (midi // 12) - 1
    note_idx = midi % 12
    return NOTE_NAMES[note_idx], octave


# Scale intervals (semitones from root)
SCALES: Dict[str, List[int]] = {
    # Major and Minor
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    
    # Modes
    "ionian": [0, 2, 4, 5, 7, 9, 11],      # Same as major
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],     # Same as natural minor
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    
    # Pentatonic
    "major_pentatonic": [0, 2, 4, 7, 9],
    "minor_pentatonic": [0, 3, 5, 7, 10],
    
    # Blues
    "blues": [0, 3, 5, 6, 7, 10],
    "blues_major": [0, 2, 3, 4, 7, 9],
    
    # Jazz/Bebop
    "bebop_dominant": [0, 2, 4, 5, 7, 9, 10, 11],
    "bebop_major": [0, 2, 4, 5, 7, 8, 9, 11],
    
    # Exotic
    "whole_tone": [0, 2, 4, 6, 8, 10],
    "diminished": [0, 2, 3, 5, 6, 8, 9, 11],      # Half-whole
    "diminished_hw": [0, 1, 3, 4, 6, 7, 9, 10],   # Whole-half
    "hungarian_minor": [0, 2, 3, 6, 7, 8, 11],
    "spanish": [0, 1, 4, 5, 7, 8, 10],
    "japanese": [0, 1, 5, 7, 8],
    "arabic": [0, 1, 4, 5, 7, 8, 11],
    
    # Chiptune/Game
    "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}


@dataclass
class Scale:
    """Represents a musical scale."""
    
    root: str
    scale_type: str
    octave: int = 4
    
    @property
    def intervals(self) -> List[int]:
        """Get the intervals for this scale type."""
        return SCALES.get(self.scale_type, SCALES["major"])
    
    @property
    def root_midi(self) -> int:
        """Get the MIDI number of the root note."""
        return note_to_midi(self.root, self.octave)
    
    def get_notes(self, octaves: int = 1) -> List[int]:
        """Get MIDI note numbers for the scale across given octaves."""
        notes = []
        for oct in range(octaves):
            base = self.root_midi + (oct * 12)
            for interval in self.intervals:
                notes.append(base + interval)
        return notes
    
    def get_note_names(self) -> List[str]:
        """Get note names for this scale."""
        root_idx = NOTE_NAMES.index(self.root.upper() if self.root.upper() in NOTE_NAMES 
                                     else ENHARMONIC.get(self.root.upper(), 'C'))
        names = []
        for interval in self.intervals:
            idx = (root_idx + interval) % 12
            names.append(NOTE_NAMES[idx])
        return names
    
    def degree_to_midi(self, degree: int, octave_offset: int = 0) -> int:
        """
        Convert scale degree to MIDI note.
        Degree 1 = root, 2 = second, etc.
        Supports negative degrees and degrees > 7.
        """
        num_notes = len(self.intervals)
        
        # Adjust for 1-based indexing
        degree_idx = degree - 1 if degree > 0 else degree
        
        # Calculate octave offset from degree
        octave_add = degree_idx // num_notes
        degree_in_scale = degree_idx % num_notes
        
        interval = self.intervals[degree_in_scale]
        return self.root_midi + interval + ((octave_offset + octave_add) * 12)
    
    def contains(self, midi_note: int) -> bool:
        """Check if a MIDI note is in this scale."""
        note_class = midi_note % 12
        root_class = self.root_midi % 12
        
        for interval in self.intervals:
            if (root_class + interval) % 12 == note_class:
                return True
        return False
    
    def nearest_in_scale(self, midi_note: int) -> int:
        """Find the nearest note that's in this scale."""
        if self.contains(midi_note):
            return midi_note
        
        # Check notes above and below
        for offset in range(1, 7):
            if self.contains(midi_note + offset):
                return midi_note + offset
            if self.contains(midi_note - offset):
                return midi_note - offset
        
        return midi_note


def get_relative_minor(major_root: str) -> str:
    """Get the relative minor of a major key."""
    root_idx = NOTE_NAMES.index(major_root.upper() if major_root.upper() in NOTE_NAMES 
                                 else ENHARMONIC.get(major_root.upper(), 'C'))
    minor_idx = (root_idx - 3) % 12
    return NOTE_NAMES[minor_idx]


def get_relative_major(minor_root: str) -> str:
    """Get the relative major of a minor key."""
    root_idx = NOTE_NAMES.index(minor_root.upper() if minor_root.upper() in NOTE_NAMES 
                                 else ENHARMONIC.get(minor_root.upper(), 'C'))
    major_idx = (root_idx + 3) % 12
    return NOTE_NAMES[major_idx]


def get_parallel_minor(major_root: str) -> str:
    """Get the parallel minor (same root) of a major key."""
    return major_root  # Same root, different scale type


# Scale synonyms for user-friendly access
SCALE_ALIASES = {
    "minor": "natural_minor",
    "pentatonic": "minor_pentatonic",
    "penta": "minor_pentatonic",
    "maj_penta": "major_pentatonic",
}


def get_scale(root: str, scale_type: str, octave: int = 4) -> Scale:
    """Factory function to create a Scale with alias support."""
    normalized_type = SCALE_ALIASES.get(scale_type.lower(), scale_type.lower())
    return Scale(root=root, scale_type=normalized_type, octave=octave)

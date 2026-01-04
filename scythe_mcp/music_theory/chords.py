"""
Scythe MCP - Chords

Chord construction, inversions, extensions, and voice leading.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from .scales import note_to_midi, midi_to_note, NOTE_NAMES, ENHARMONIC


# Chord intervals from root (in semitones)
CHORD_TYPES: Dict[str, List[int]] = {
    # Triads
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    
    # Seventh chords
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "7": [0, 4, 7, 10],        # Dominant 7
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],     # Half-diminished
    "minmaj7": [0, 3, 7, 11],
    "aug7": [0, 4, 8, 10],
    
    # Extended chords
    "9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "min9": [0, 3, 7, 10, 14],
    "11": [0, 4, 7, 10, 14, 17],
    "min11": [0, 3, 7, 10, 14, 17],
    "13": [0, 4, 7, 10, 14, 17, 21],
    "maj13": [0, 4, 7, 11, 14, 17, 21],
    
    # Add chords
    "add9": [0, 4, 7, 14],
    "add11": [0, 4, 7, 17],
    "madd9": [0, 3, 7, 14],
    
    # Altered chords
    "7b9": [0, 4, 7, 10, 13],
    "7#9": [0, 4, 7, 10, 15],
    "7#11": [0, 4, 7, 10, 18],
    "7b13": [0, 4, 7, 10, 20],
    "7alt": [0, 4, 6, 10, 13, 15],  # Altered dominant
    
    # Power chords (common in rock/metal)
    "5": [0, 7],
    "power": [0, 7, 12],
    
    # Shoegaze/Dream pop favorites
    "add9sus4": [0, 5, 7, 14],
    "7sus4": [0, 5, 7, 10],
}

# Chord symbol aliases
CHORD_ALIASES = {
    "m": "minor",
    "M": "major",
    "-": "minor",
    "o": "diminished",
    "+": "augmented",
    "dom7": "7",
    "Δ7": "maj7",
    "Δ": "maj7",
    "-7": "min7",
    "ø": "m7b5",
    "ø7": "m7b5",
    "o7": "dim7",
}


@dataclass
class Chord:
    """Represents a musical chord."""
    
    root: str
    chord_type: str = "major"
    octave: int = 4
    inversion: int = 0
    voicing: Optional[List[int]] = None
    
    @property
    def intervals(self) -> List[int]:
        """Get the intervals for this chord type."""
        chord_key = CHORD_ALIASES.get(self.chord_type, self.chord_type)
        return CHORD_TYPES.get(chord_key, CHORD_TYPES["major"])
    
    @property
    def root_midi(self) -> int:
        """Get the MIDI number of the root note."""
        return note_to_midi(self.root, self.octave)
    
    def get_notes(self) -> List[int]:
        """Get MIDI note numbers for this chord."""
        base_notes = [self.root_midi + interval for interval in self.intervals]
        
        # Apply inversion
        if self.inversion > 0:
            inv = self.inversion % len(base_notes)
            # Move bottom notes up an octave
            for i in range(inv):
                base_notes[i] += 12
            base_notes.sort()
        
        # Apply custom voicing if specified
        if self.voicing:
            return [base_notes[i % len(base_notes)] + (12 * (i // len(base_notes))) 
                    for i in self.voicing]
        
        return base_notes
    
    def get_note_names(self) -> List[str]:
        """Get note names for this chord."""
        midi_notes = self.get_notes()
        return [midi_to_note(n)[0] for n in midi_notes]
    
    @property
    def name(self) -> str:
        """Get the full chord name."""
        type_display = {
            "major": "",
            "minor": "m",
            "diminished": "dim",
            "augmented": "aug",
            "7": "7",
            "maj7": "maj7",
            "min7": "m7",
        }.get(self.chord_type, self.chord_type)
        
        inv_display = ""
        if self.inversion > 0:
            inv_names = ["", "/3", "/5", "/7"]
            inv_display = inv_names[self.inversion] if self.inversion < len(inv_names) else f"/{self.inversion}"
        
        return f"{self.root}{type_display}{inv_display}"
    
    def with_bass(self, bass_note: str) -> "Chord":
        """Create a slash chord with a specific bass note."""
        # Calculate which inversion puts the bass note at the bottom
        bass_interval = (note_to_midi(bass_note, 0) - note_to_midi(self.root, 0)) % 12
        
        for i, interval in enumerate(self.intervals):
            if interval % 12 == bass_interval:
                return Chord(
                    root=self.root,
                    chord_type=self.chord_type,
                    octave=self.octave,
                    inversion=i
                )
        
        # Bass note not in chord - create voicing with added bass
        return self  # Fallback


def voice_lead(from_chord: Chord, to_chord: Chord) -> Chord:
    """
    Apply voice leading to minimize movement between chords.
    Returns a new chord with optimized voicing.
    """
    from_notes = from_chord.get_notes()
    to_notes = to_chord.get_notes()
    
    best_voicing = None
    min_movement = float('inf')
    
    # Try all inversions
    for inv in range(len(to_chord.intervals)):
        test_chord = Chord(
            root=to_chord.root,
            chord_type=to_chord.chord_type,
            octave=to_chord.octave,
            inversion=inv
        )
        test_notes = test_chord.get_notes()
        
        # Calculate total movement
        movement = 0
        for from_note in from_notes:
            closest = min(test_notes, key=lambda n: abs(n - from_note))
            movement += abs(closest - from_note)
        
        if movement < min_movement:
            min_movement = movement
            best_voicing = inv
    
    return Chord(
        root=to_chord.root,
        chord_type=to_chord.chord_type,
        octave=to_chord.octave,
        inversion=best_voicing or 0
    )


def parse_chord(chord_str: str) -> Chord:
    """
    Parse a chord string like "Cmaj7", "Dm", "F#m7b5".
    """
    chord_str = chord_str.strip()
    if not chord_str:
        return Chord("C", "major")
    
    # Extract root note
    root = chord_str[0].upper()
    idx = 1
    
    # Check for sharp/flat
    if len(chord_str) > 1 and chord_str[1] in '#b':
        root += chord_str[1]
        idx = 2
    
    # Rest is the chord type
    chord_type_str = chord_str[idx:].lower() if idx < len(chord_str) else ""
    
    # Map to chord type
    chord_type = "major"
    if chord_type_str in CHORD_TYPES:
        chord_type = chord_type_str
    elif chord_type_str in CHORD_ALIASES:
        chord_type = CHORD_ALIASES[chord_type_str]
    elif chord_type_str.startswith("m") and not chord_type_str.startswith("maj"):
        if chord_type_str in ("m", "min"):
            chord_type = "minor"
        else:
            # Try with 'min' prefix
            rest = chord_type_str[1:]
            if f"min{rest}" in CHORD_TYPES:
                chord_type = f"min{rest}"
            elif f"m{rest}" in CHORD_TYPES:
                chord_type = f"m{rest}"
    
    return Chord(root=root, chord_type=chord_type)


# Common chord voicings for different styles
VOICINGS = {
    "open": {
        "major": [0, 7, 12, 16],  # Root, 5th, octave, 3rd
        "minor": [0, 7, 12, 15],
    },
    "closed": {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
    },
    "drop2": {
        "maj7": [0, 7, 11, 16],
        "min7": [0, 7, 10, 15],
    },
    "shell": {  # Jazz shell voicings (root, 3rd, 7th)
        "maj7": [0, 4, 11],
        "min7": [0, 3, 10],
        "7": [0, 4, 10],
    }
}

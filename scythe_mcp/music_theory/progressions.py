"""
Scythe MCP - Chord Progressions

Common progressions, genre-specific patterns, and modulation helpers.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .chords import Chord, parse_chord, voice_lead


# Roman numeral to scale degree mapping
ROMAN_NUMERALS = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7,
}

# Scale degree to chord quality in major key
MAJOR_KEY_CHORDS = {
    1: "major", 2: "minor", 3: "minor", 4: "major",
    5: "major", 6: "minor", 7: "diminished"
}

# Scale degree to chord quality in minor key
MINOR_KEY_CHORDS = {
    1: "minor", 2: "diminished", 3: "major", 4: "minor",
    5: "minor", 6: "major", 7: "major"
}

# Common progressions by genre (in Roman numerals for transposition)
COMMON_PROGRESSIONS: Dict[str, Dict[str, List[str]]] = {
    "pop": {
        "axis": ["I", "V", "vi", "IV"],          # Axis of Awesome
        "classic": ["I", "IV", "V", "I"],
        "sensitive": ["vi", "IV", "I", "V"],
        "doo_wop": ["I", "vi", "IV", "V"],
    },
    "jazz": {
        "ii_v_i": ["ii7", "V7", "Imaj7"],
        "ii_v_i_vi": ["ii7", "V7", "Imaj7", "vi7"],
        "rhythm_changes_a": ["Imaj7", "vi7", "ii7", "V7"],
        "minor_ii_v_i": ["iiø7", "V7b9", "i7"],
        "turnaround": ["Imaj7", "vi7", "ii7", "V7"],
        "backdoor": ["Imaj7", "bVII7", "Imaj7"],
        "coltrane": ["Imaj7", "bIIImaj7", "Vmaj7"],  # Giant Steps
    },
    "blues": {
        "12_bar": ["I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7"],
        "quick_change": ["I7", "IV7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7"],
        "minor_blues": ["i7", "i7", "i7", "i7", "iv7", "iv7", "i7", "i7", "VI7", "V7", "i7", "V7"],
    },
    "rock": {
        "classic": ["I", "IV", "V", "I"],
        "power": ["I5", "bVII5", "IV5", "I5"],
        "grunge": ["I", "IV", "bVI", "bVII"],
        "modal": ["i", "bVII", "bVI", "bVII"],
    },
    "lofi": {
        "chill": ["ii7", "V7", "Imaj7", "vi7"],
        "melancholic": ["i9", "bVI9", "III9", "bVII9"],
        "jazzy": ["IVmaj7", "iii7", "vi7", "ii7"],
        "dreamy": ["Imaj7", "ii7", "iii7", "IVmaj7"],
    },
    "electronic": {
        "trance": ["i", "bVI", "bVII", "i"],
        "house": ["i", "i", "bVI", "bVII"],
        "edm_drop": ["vi", "IV", "I", "V"],
        "techno": ["i", "bVII", "bVI", "V"],
    },
    "shoegaze": {
        "wall": ["I", "iii", "IV", "ii"],
        "ethereal": ["Iadd9", "IVadd9", "vi", "V"],
        "dreamy": ["I", "bVII", "IV", "I"],
    },
    "dreampop": {
        "lush": ["Imaj7", "IVmaj7add9", "vi7", "IV"],
        "nostalgic": ["I", "vi", "IV", "iii"],
    },
    "emo": {
        "classic": ["I", "vi", "IV", "V"],
        "midwest": ["I", "V", "vi", "IV"],
        "post": ["i", "III", "bVII", "IV"],
    },
    "folk": {
        "simple": ["I", "IV", "V", "I"],
        "storytelling": ["I", "V", "vi", "IV"],
        "modal": ["i", "bVII", "i", "iv"],
    },
    "chiptune": {
        "heroic": ["I", "IV", "V", "I"],
        "boss_battle": ["i", "bVI", "bVII", "i"],
        "victory": ["I", "IV", "I", "V", "I"],
    },
    "ambient": {
        "drone": ["I", "I", "I", "I"],  # Static harmony
        "evolving": ["Imaj7", "IVmaj7", "Imaj7", "Vmaj7"],
        "cinematic": ["i", "bVI", "IV", "i"],
    },
}


@dataclass
class Progression:
    """Represents a chord progression."""
    
    key: str
    mode: str  # "major" or "minor"
    chords: List[str]  # Roman numerals or chord names
    bars_per_chord: int = 1
    
    def to_chords(self, octave: int = 4) -> List[Chord]:
        """Convert Roman numerals to actual Chord objects."""
        from .scales import NOTE_NAMES, ENHARMONIC
        
        result = []
        key_idx = NOTE_NAMES.index(
            self.key.upper() if self.key.upper() in NOTE_NAMES 
            else ENHARMONIC.get(self.key.upper(), 'C')
        )
        
        scale_intervals = [0, 2, 4, 5, 7, 9, 11] if self.mode == "major" else [0, 2, 3, 5, 7, 8, 10]
        chord_qualities = MAJOR_KEY_CHORDS if self.mode == "major" else MINOR_KEY_CHORDS
        
        for numeral in self.chords:
            chord = self._parse_roman_numeral(numeral, key_idx, scale_intervals, chord_qualities, octave)
            result.append(chord)
        
        return result
    
    def _parse_roman_numeral(
        self, 
        numeral: str, 
        key_idx: int, 
        scale_intervals: List[int],
        chord_qualities: Dict[int, str],
        octave: int
    ) -> Chord:
        """Parse a Roman numeral chord symbol."""
        from .scales import NOTE_NAMES
        
        # Handle flats/sharps
        modifier = 0
        if numeral.startswith('b'):
            modifier = -1
            numeral = numeral[1:]
        elif numeral.startswith('#'):
            modifier = 1
            numeral = numeral[1:]
        
        # Extract base numeral
        base_numeral = ""
        for char in numeral:
            if char.upper() in "IVX":
                base_numeral += char
            else:
                break
        
        remainder = numeral[len(base_numeral):]
        
        # Get scale degree
        degree = ROMAN_NUMERALS.get(base_numeral.upper(), 1)
        is_minor = base_numeral.islower()
        
        # Calculate root note
        interval = scale_intervals[degree - 1] + modifier
        root_idx = (key_idx + interval) % 12
        root = NOTE_NAMES[root_idx]
        
        # Determine chord quality
        if remainder:
            # Explicit chord type in Roman numeral
            chord_type = remainder.replace("ø", "m7b5").lower()
            if chord_type == "7" and is_minor:
                chord_type = "min7"
            elif chord_type == "7":
                chord_type = "7"  # Dominant
            elif chord_type == "maj7":
                chord_type = "maj7"
        else:
            # Infer from numeral case
            chord_type = "minor" if is_minor else "major"
        
        return Chord(root=root, chord_type=chord_type, octave=octave)
    
    def with_voice_leading(self, octave: int = 4) -> List[Chord]:
        """Get chords with optimized voice leading."""
        raw_chords = self.to_chords(octave)
        if len(raw_chords) < 2:
            return raw_chords
        
        result = [raw_chords[0]]
        for chord in raw_chords[1:]:
            voiced = voice_lead(result[-1], chord)
            result.append(voiced)
        
        return result


def get_progression(
    key: str,
    genre: str,
    style: str = None,
    mode: str = "major"
) -> Progression:
    """Get a chord progression for a genre/style."""
    genre_progs = COMMON_PROGRESSIONS.get(genre.lower(), COMMON_PROGRESSIONS["pop"])
    
    if style:
        chords = genre_progs.get(style, list(genre_progs.values())[0])
    else:
        # Get first progression for genre
        chords = list(genre_progs.values())[0]
    
    return Progression(key=key, mode=mode, chords=chords)


# Modulation helpers
def modulate_up_half_step(key: str) -> str:
    """Modulate up by a half step."""
    from .scales import NOTE_NAMES
    key_idx = NOTE_NAMES.index(key.upper() if key.upper() in NOTE_NAMES else 'C')
    return NOTE_NAMES[(key_idx + 1) % 12]


def modulate_to_relative_minor(major_key: str) -> str:
    """Get the relative minor of a major key."""
    from .scales import NOTE_NAMES
    key_idx = NOTE_NAMES.index(major_key.upper() if major_key.upper() in NOTE_NAMES else 'C')
    return NOTE_NAMES[(key_idx - 3) % 12]


def modulate_to_relative_major(minor_key: str) -> str:
    """Get the relative major of a minor key."""
    from .scales import NOTE_NAMES
    key_idx = NOTE_NAMES.index(minor_key.upper() if minor_key.upper() in NOTE_NAMES else 'A')
    return NOTE_NAMES[(key_idx + 3) % 12]


def modulate_circle_of_fifths(key: str, steps: int = 1) -> str:
    """Move around the circle of fifths."""
    from .scales import NOTE_NAMES
    key_idx = NOTE_NAMES.index(key.upper() if key.upper() in NOTE_NAMES else 'C')
    # Each step is 7 semitones up (fifth) or 5 semitones down (fourth)
    return NOTE_NAMES[(key_idx + (7 * steps)) % 12]

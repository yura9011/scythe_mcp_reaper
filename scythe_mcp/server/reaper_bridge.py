"""
Scythe MCP - REAPER Bridge via OSC + File Commands

Uses OSC for transport/basic commands and file-based polling for complex operations.
"""

import os
import json
import time
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    from pythonosc import udp_client
    from pythonosc.osc_message_builder import OscMessageBuilder
    HAS_OSC = True
except ImportError:
    HAS_OSC = False

logger = logging.getLogger("ScytheMCP")


# REAPER Action IDs (from REAPER Action List)
REAPER_ACTIONS = {
    # Transport
    "play": 1007,
    "stop": 1016,
    "pause": 1008,
    "record": 1013,
    "rewind": 40042,
    "forward": 40043,
    "goto_start": 40042,
    "goto_end": 40043,
    
    # Tracks
    "insert_track": 40001,
    "insert_midi_track": 40001,  # Same as insert track
    "delete_track": 40005,
    "duplicate_track": 40062,
    
    # Items
    "insert_empty_item": 40142,
    "split_items": 40012,
    "delete_items": 40006,
    
    # View
    "zoom_fit": 40295,
    "toggle_mixer": 40078,
    
    # Project
    "save": 40026,
    "save_as": 40022,
    "new_project": 40023,
    "undo": 40029,
    "redo": 40030,
}


@dataclass
class ReaperBridge:
    """Bridge to REAPER using OSC and file-based commands."""
    
    osc_host: str = None  # Set via REAPER_OSC_HOST env or default to 127.0.0.1
    osc_port: int = None  # Set via REAPER_OSC_PORT env or default to 8000
    command_file: Path = None
    response_file: Path = None
    
    _osc_client: Any = None
    
    def __post_init__(self):
        # Configure OSC from environment or defaults
        if self.osc_host is None:
            self.osc_host = os.environ.get("REAPER_OSC_HOST", "127.0.0.1")
        if self.osc_port is None:
            self.osc_port = int(os.environ.get("REAPER_OSC_PORT", "8000"))
        
        # Use temp directory for command files
        temp_dir = Path(tempfile.gettempdir()) / "scythe_mcp"
        temp_dir.mkdir(exist_ok=True)
        
        self.command_file = temp_dir / "command.json"
        self.response_file = temp_dir / "response.json"
        
        # Initialize OSC client
        if HAS_OSC:
            try:
                self._osc_client = udp_client.SimpleUDPClient(self.osc_host, self.osc_port)
                logger.info(f"OSC client ready: {self.osc_host}:{self.osc_port}")
            except Exception as e:
                logger.warning(f"OSC init failed: {e}")
                self._osc_client = None
    
    def send_osc(self, address: str, *args) -> bool:
        """Send an OSC message to REAPER."""
        if not self._osc_client:
            logger.warning("OSC client not available")
            return False
        
        try:
            self._osc_client.send_message(address, args if args else [])
            return True
        except Exception as e:
            logger.error(f"OSC send failed: {e}")
            return False
    
    def trigger_action(self, action_id: int) -> bool:
        """Trigger a REAPER action by ID."""
        # OSC format: /action/_ID or /action/ID
        return self.send_osc(f"/action/{action_id}")
    
    def trigger_action_by_name(self, name: str) -> bool:
        """Trigger a REAPER action by name."""
        action_id = REAPER_ACTIONS.get(name.lower())
        if action_id:
            return self.trigger_action(action_id)
        logger.warning(f"Unknown action: {name}")
        return False
    
    # ==========================================================================
    # TRANSPORT (OSC native)
    # ==========================================================================
    
    def play(self) -> bool:
        """Start playback."""
        return self.send_osc("/play")
    
    def stop(self) -> bool:
        """Stop playback."""
        return self.send_osc("/stop")
    
    def record(self) -> bool:
        """Start recording."""
        return self.send_osc("/record")
    
    def pause(self) -> bool:
        """Toggle pause."""
        return self.send_osc("/pause")
    
    def set_tempo(self, bpm: float) -> bool:
        """Set project tempo."""
        return self.send_osc("/tempo/raw", float(bpm))
    
    def goto_position(self, seconds: float) -> bool:
        """Move cursor to position in seconds."""
        return self.send_osc("/time", float(seconds))
    
    def goto_beat(self, beat: float) -> bool:
        """Move cursor to beat position."""
        return self.send_osc("/beat", float(beat))
    
    # ==========================================================================
    # TRACKS (OSC native)
    # ==========================================================================
    
    def set_track_volume(self, track_index: int, volume: float) -> bool:
        """Set track volume (0.0 to 1.0 normalized)."""
        # REAPER OSC: /track/N/volume
        return self.send_osc(f"/track/{track_index + 1}/volume", float(volume))
    
    def set_track_pan(self, track_index: int, pan: float) -> bool:
        """Set track pan (-1.0 to 1.0)."""
        return self.send_osc(f"/track/{track_index + 1}/pan", float(pan))
    
    def set_track_mute(self, track_index: int, muted: bool) -> bool:
        """Mute/unmute track."""
        return self.send_osc(f"/track/{track_index + 1}/mute", 1 if muted else 0)
    
    def set_track_solo(self, track_index: int, solo: bool) -> bool:
        """Solo/unsolo track."""
        return self.send_osc(f"/track/{track_index + 1}/solo", 1 if solo else 0)
    
    def set_track_arm(self, track_index: int, armed: bool) -> bool:
        """Arm/disarm track for recording."""
        return self.send_osc(f"/track/{track_index + 1}/recarm", 1 if armed else 0)
    
    def select_track(self, track_index: int) -> bool:
        """Select a track."""
        return self.send_osc(f"/track/{track_index + 1}/select", 1)
    
    # ==========================================================================
    # FILE-BASED COMMANDS (for complex operations)
    # ==========================================================================
    
    def _write_command(self, command: str, params: Dict[str, Any]) -> bool:
        """Write a command to the file for Lua to pick up."""
        try:
            cmd_data = {
                "command": command,
                "params": params,
                "timestamp": time.time()
            }
            self.command_file.write_text(json.dumps(cmd_data, indent=2))
            return True
        except Exception as e:
            logger.error(f"Failed to write command: {e}")
            return False
    
    def _read_response(self, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        """Read response from Lua script."""
        start = time.time()
        
        # Clear old response
        if self.response_file.exists():
            self.response_file.unlink()
        
        while time.time() - start < timeout:
            if self.response_file.exists():
                try:
                    data = json.loads(self.response_file.read_text())
                    return data
                except:
                    pass
            time.sleep(0.05)
        
        return None
    
    def create_track(self, name: str = "New Track") -> Dict[str, Any]:
        """Create a new track via action then file command for naming."""
        # First trigger insert track action
        self.trigger_action(40001)
        
        # Then send naming command via file
        self._write_command("name_selected_track", {"name": name})
        
        return {"success": True, "message": f"Created track: {name}"}
    
    def insert_midi_item(self, track_index: int, position: float, length: float) -> Dict[str, Any]:
        """Insert MIDI item via file command."""
        self._write_command("insert_midi_item", {
            "track_index": track_index,
            "position": position,
            "length": length
        })
        
        response = self._read_response()
        if response:
            return response
        return {"success": True, "message": "MIDI item command sent"}
    
    def add_notes(self, track_index: int, item_index: int, notes: List[Dict]) -> Dict[str, Any]:
        """Add MIDI notes via file command."""
        self._write_command("add_notes", {
            "track_index": track_index,
            "item_index": item_index,
            "notes": notes
        })
        
        response = self._read_response()
        if response:
            return response
        return {"success": True, "message": "Notes command sent"}
    
    def execute_lua(self, code: str) -> Dict[str, Any]:
        """Execute arbitrary Lua code in REAPER."""
        self._write_command("execute_lua", {"code": code})
        
        response = self._read_response(timeout=5.0)
        if response:
            return response
        return {"success": True, "message": "Lua code sent for execution"}


# Global instance
_bridge: Optional[ReaperBridge] = None


def get_bridge() -> ReaperBridge:
    """Get or create the REAPER bridge."""
    global _bridge
    if _bridge is None:
        _bridge = ReaperBridge()
    return _bridge

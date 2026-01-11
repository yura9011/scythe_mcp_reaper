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
    temp_dir: Path = None
    
    _osc_client: Any = None
    
    def __post_init__(self):
        # Configure OSC from environment or defaults
        if self.osc_host is None:
            self.osc_host = os.environ.get("REAPER_OSC_HOST", "127.0.0.1")
        if self.osc_port is None:
            self.osc_port = int(os.environ.get("REAPER_OSC_PORT", "8000"))
        
        # Use temp directory for command files
        self.temp_dir = Path(tempfile.gettempdir()) / "scythe_mcp"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.command_file = self.temp_dir / "command.json"
        self.response_file = self.temp_dir / "response.json"
        
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
        """Create a new track via Lua for strict synchronous execution."""
        # We use a Lua script to insert the track at the end and return its index
        lua_code = f"""
        local idx = reaper.CountTracks(0)
        -- return "DEBUG: Count " .. tostring(idx)
        reaper.InsertTrackAtIndex(idx, true)
        local track = reaper.GetTrack(0, idx)
        if track then
            reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "{name}", true)
            reaper.TrackList_AdjustWindows(false)
            reaper.UpdateArrange()
            return idx
        end
        return "ERROR: Track not found after insert at " .. tostring(idx)
        """
        # We use execute_lua which waits for response
        result = self.execute_lua(lua_code)
        
        # Check result
        if result.get("success"):
            val = result.get("result", "ERROR")
            if "ERROR" not in str(val) and "DEBUG" not in str(val):
                try:
                    idx = int(float(str(val)))
                    if idx >= 0:
                        return {
                            "success": True, 
                            "message": f"Created track: {name}", 
                            "track_index": idx
                        }
                except ValueError:
                    pass
        
        return {"success": False, "message": f"Failed to create track via Lua. Res: {result}"}
    
    def insert_midi_item(self, track_index: int, position: float, length: float) -> Dict[str, Any]:
        """Insert MIDI item via direct Lua execution for consistency."""
        lua_code = f"""
        local track = reaper.GetTrack(0, {track_index})
        if not track then return "ERROR: Track not found" end
        
        local tempo = reaper.Master_GetTempo()
        local pos_sec = {position} * (60 / tempo)
        local len_sec = {length} * (60 / tempo)
        
        local item = reaper.CreateNewMIDIItemInProj(track, pos_sec, pos_sec + len_sec, false)
        if item then
            local take = reaper.GetActiveTake(item)
            if take then
                reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", "Generated MIDI", true)
            end
            reaper.UpdateArrange()
            reaper.TrackList_AdjustWindows(false)
            return "Success: Item Created on Track " .. {track_index}
        end
        return "ERROR: Failed to create item"
        """
        
        result = self.execute_lua(lua_code)
        
        if result.get("success"):
             # Map string success to consistent response
             return result
        return {"success": False, "message": f"Failed to insert item. Res: {result}"}
    
    def add_notes(self, track_index: int, item_index: int, notes: List[Dict]) -> Dict[str, Any]:
        """Add MIDI notes via execute_lua to bypass complex JSON parsing."""
        
        # Construct Lua table of notes
        # Each note: {pitch, start, duration, velocity}
        # We'll generate a Lua script that iterates this
        
        lua_notes = []
        for n in notes:
            # pitch, start(beats), duration(beats), velocity
            pitch = int(n.get("pitch", 60))
            start = float(n.get("start", 0.0))
            dur = float(n.get("duration", 1.0))
            vel = int(n.get("velocity", 100))
            lua_notes.append(f"{{p={pitch},s={start},d={dur},v={vel}}}")
        
        notes_str = "{" + ",".join(lua_notes) + "}"
        
        lua_code = f"""
        local log = ""
        local function debug(msg) log = log .. msg .. "\\n" end
        
        debug("Start add_notes for Track " .. {track_index} .. " Item " .. {item_index})
        local track = reaper.GetTrack(0, {track_index})
        if track then
            debug("Track found")
            local item = reaper.GetTrackMediaItem(track, {item_index})
            if item then
                debug("Item found")
                local take = reaper.GetActiveTake(item)
                if take then
                    debug("Take found")
                    local ppq = 960 -- Standard resolution
                    local notes = {notes_str}
                    debug("Processing " .. #notes .. " notes")
                    
                    local count = 0
                    for i, note in ipairs(notes) do
                        local start_ppq = math.floor(note.s * ppq)
                        local end_ppq = math.floor((note.s + note.d) * ppq)
                        reaper.MIDI_InsertNote(take, false, false, start_ppq, end_ppq, 0, note.p, note.v, true)
                        count = count + 1
                    end
                    debug("Inserted " .. count .. " notes")
                    
                    reaper.MIDI_Sort(take)
                    reaper.UpdateArrange()
                    return "Success: " .. log
                else
                    return "ERROR: No active take on item"
                end
            else
                local cnt = reaper.CountTrackMediaItems(track)
                return "ERROR: Item " .. {item_index} .. " not found. Track has " .. cnt .. " items."
            end
        else
            return "ERROR: Track " .. {track_index} .. " not found"
        end
        """
        
        return self.execute_lua(lua_code)
    
    def execute_lua(self, code: str) -> Dict[str, Any]:
        """Execute Lua code in REAPER via file transfer (robust)."""
        # Write code to a temp file
        import uuid
        code_filename = f"lua_{uuid.uuid4().hex}.lua"
        code_path = self.temp_dir / code_filename
        code_path.write_text(code, encoding="utf-8")
        
        # Send path to REAPER
        self._write_command("run_lua_file", {"path": str(code_path)})
        
        response = self._read_response(timeout=5.0)
        
        # Cleanup
        try:
            code_path.unlink()
        except:
            pass
            
        if response:
            return response
        return {"success": True, "message": "Lua file execution sent"}


# Global instance
_bridge: Optional[ReaperBridge] = None


def get_bridge() -> ReaperBridge:
    """Get or create the REAPER bridge."""
    global _bridge
    if _bridge is None:
        _bridge = ReaperBridge()
    return _bridge

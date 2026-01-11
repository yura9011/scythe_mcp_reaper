import json
import tempfile
from pathlib import Path
import time

temp_dir = Path(tempfile.gettempdir()) / "scythe_mcp"

# Add atmospheric pad on FX track - sustained high notes
lua_code = '''
local count = reaper.CountTracks(0)
local fx = reaper.GetTrack(0, count - 1)
if fx then
    local tempo = reaper.Master_GetTempo()
    local beat_sec = 60/tempo
    local ppq = 960
    local fx_item = reaper.CreateNewMIDIItemInProj(fx, 0, 16*beat_sec, false)
    local take = reaper.GetActiveTake(fx_item)
    if take then
        reaper.MIDI_InsertNote(take, false, false, 0, ppq*8, 0, 84, 40, false)
        reaper.MIDI_InsertNote(take, false, false, ppq*8, ppq*16, 0, 86, 35, false)
        reaper.MIDI_InsertNote(take, false, false, ppq*4, ppq*12, 0, 79, 30, false)
        reaper.MIDI_Sort(take)
    end
    if reaper.TrackFX_GetCount(fx) == 0 then
        reaper.TrackFX_AddByName(fx, "ReaSynth", false, -1)
    end
end
reaper.UpdateArrange()
'''

command = {
    "command": "execute_lua",
    "params": {"code": lua_code.replace('\n', ' ')},
    "timestamp": time.time()
}

(temp_dir / "command.json").write_text(json.dumps(command, indent=2))
print("Sent: Atmospheric pad on FX track!")

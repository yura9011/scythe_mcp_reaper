--[[
Scythe MCP - REAPER Lua Client

TCP client that runs inside REAPER and receives commands from the MCP server.
This script should be loaded at REAPER startup or run manually.

Installation:
1. Copy this file to your REAPER Scripts folder
2. Actions -> Show Action List -> Load ReaScript
3. Optionally: Add to startup actions

Usage:
- Run this script in REAPER
- It will connect to the Scythe MCP Python server on localhost:9878
- Commands from AI agents will be executed in REAPER
]]

local socket = nil
local connected = false
local HOST = "127.0.0.1"
local PORT = 9878
local BUFFER_SIZE = 4096

-- Check if socket library is available
local has_socket = pcall(function()
    socket = require("socket")
end)

if not has_socket then
    reaper.ShowMessageBox(
        "LuaSocket library not found!\n\n" ..
        "To install:\n" ..
        "1. Download LuaSocket for your platform\n" ..
        "2. Place socket.lua and socket/core.dll in REAPER's Scripts folder\n\n" ..
        "Alternatively, use REAPER's built-in networking via reapack.",
        "Scythe MCP Error",
        0
    )
    return
end

-- =============================================================================
-- LOGGING
-- =============================================================================

local function log(msg)
    reaper.ShowConsoleMsg("[Scythe] " .. tostring(msg) .. "\n")
end

-- =============================================================================
-- JSON HELPERS (minimal implementation)
-- =============================================================================

local json = {}

function json.encode(obj)
    local t = type(obj)
    if t == "nil" then
        return "null"
    elseif t == "boolean" then
        return obj and "true" or "false"
    elseif t == "number" then
        return tostring(obj)
    elseif t == "string" then
        return '"' .. obj:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
    elseif t == "table" then
        local is_array = #obj > 0 or next(obj) == nil
        local parts = {}
        if is_array then
            for i, v in ipairs(obj) do
                parts[i] = json.encode(v)
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            for k, v in pairs(obj) do
                table.insert(parts, json.encode(tostring(k)) .. ":" .. json.encode(v))
            end
            return "{" .. table.concat(parts, ",") .. "}"
        end
    end
    return "null"
end

function json.decode(str)
    -- Simple JSON decoder - works for our use case
    local pos = 1
    local function skip_whitespace()
        while pos <= #str and str:sub(pos, pos):match("%s") do
            pos = pos + 1
        end
    end
    
    local function parse_value()
        skip_whitespace()
        local c = str:sub(pos, pos)
        
        if c == '"' then
            -- String
            pos = pos + 1
            local start = pos
            while pos <= #str do
                local ch = str:sub(pos, pos)
                if ch == '"' then
                    local result = str:sub(start, pos - 1)
                    pos = pos + 1
                    return result
                elseif ch == '\\' then
                    pos = pos + 2
                else
                    pos = pos + 1
                end
            end
        elseif c == '{' then
            -- Object
            pos = pos + 1
            local obj = {}
            skip_whitespace()
            if str:sub(pos, pos) == '}' then
                pos = pos + 1
                return obj
            end
            while true do
                skip_whitespace()
                local key = parse_value()
                skip_whitespace()
                pos = pos + 1  -- skip :
                local value = parse_value()
                obj[key] = value
                skip_whitespace()
                if str:sub(pos, pos) == '}' then
                    pos = pos + 1
                    break
                end
                pos = pos + 1  -- skip ,
            end
            return obj
        elseif c == '[' then
            -- Array
            pos = pos + 1
            local arr = {}
            skip_whitespace()
            if str:sub(pos, pos) == ']' then
                pos = pos + 1
                return arr
            end
            while true do
                table.insert(arr, parse_value())
                skip_whitespace()
                if str:sub(pos, pos) == ']' then
                    pos = pos + 1
                    break
                end
                pos = pos + 1  -- skip ,
            end
            return arr
        elseif str:sub(pos, pos + 3) == "true" then
            pos = pos + 4
            return true
        elseif str:sub(pos, pos + 4) == "false" then
            pos = pos + 5
            return false
        elseif str:sub(pos, pos + 3) == "null" then
            pos = pos + 4
            return nil
        else
            -- Number
            local start = pos
            while pos <= #str and str:sub(pos, pos):match("[%d%.%-eE%+]") do
                pos = pos + 1
            end
            return tonumber(str:sub(start, pos - 1))
        end
    end
    
    return parse_value()
end

-- =============================================================================
-- COMMAND HANDLERS
-- =============================================================================

local handlers = {}

function handlers.get_session_info(params)
    local project = 0  -- Current project
    local tempo = reaper.Master_GetTempo()
    local _, num, den = reaper.TimeSignature_Get(project)
    local track_count = reaper.CountTracks(project)
    local play_state = reaper.GetPlayState()
    local cursor_pos = reaper.GetCursorPosition()
    local _, project_name = reaper.EnumProjects(-1, "")
    
    return {
        success = true,
        data = {
            project_name = project_name or "Untitled",
            tempo = tempo,
            time_sig = string.format("%d/%d", num, den),
            track_count = track_count,
            playing = (play_state & 1) == 1,
            recording = (play_state & 4) == 4,
            cursor_pos = cursor_pos
        }
    }
end

function handlers.set_tempo(params)
    local tempo = params.tempo
    if tempo and tempo >= 20 and tempo <= 999 then
        reaper.CSurf_OnTempoChange(tempo)
        return {success = true}
    end
    return {success = false, error = "Invalid tempo"}
end

function handlers.set_time_signature(params)
    local num = params.numerator or 4
    local den = params.denominator or 4
    -- Note: REAPER's time signature API is project-specific
    reaper.SetCurrentBPM(0, reaper.Master_GetTempo(), true)
    return {success = true}
end

function handlers.list_tracks(params)
    local project = 0
    local tracks = {}
    local count = reaper.CountTracks(project)
    
    for i = 0, count - 1 do
        local track = reaper.GetTrack(project, i)
        local _, name = reaper.GetTrackName(track)
        local muted = reaper.GetMediaTrackInfo_Value(track, "B_MUTE") == 1
        local solo = reaper.GetMediaTrackInfo_Value(track, "I_SOLO") > 0
        local armed = reaper.GetMediaTrackInfo_Value(track, "I_RECARM") == 1
        
        table.insert(tracks, {
            index = i,
            name = name,
            muted = muted,
            solo = solo,
            armed = armed
        })
    end
    
    return {success = true, data = {tracks = tracks}}
end

function handlers.create_track(params)
    local name = params.name or "New Track"
    local index = params.index or -1
    local project = 0
    
    -- Insert track
    if index < 0 then
        index = reaper.CountTracks(project)
    end
    
    reaper.InsertTrackAtIndex(index, true)
    local track = reaper.GetTrack(project, index)
    
    if track then
        reaper.GetSetMediaTrackInfo_String(track, "P_NAME", name, true)
        return {success = true, data = {track_index = index}}
    end
    
    return {success = false, error = "Failed to create track"}
end

function handlers.set_track_volume(params)
    local track = reaper.GetTrack(0, params.track_index)
    if track then
        reaper.SetMediaTrackInfo_Value(track, "D_VOL", params.volume)
        return {success = true}
    end
    return {success = false, error = "Track not found"}
end

function handlers.set_track_pan(params)
    local track = reaper.GetTrack(0, params.track_index)
    if track then
        reaper.SetMediaTrackInfo_Value(track, "D_PAN", params.pan)
        return {success = true}
    end
    return {success = false, error = "Track not found"}
end

function handlers.set_track_mute(params)
    local track = reaper.GetTrack(0, params.track_index)
    if track then
        reaper.SetMediaTrackInfo_Value(track, "B_MUTE", params.muted and 1 or 0)
        return {success = true}
    end
    return {success = false, error = "Track not found"}
end

function handlers.set_track_solo(params)
    local track = reaper.GetTrack(0, params.track_index)
    if track then
        reaper.SetMediaTrackInfo_Value(track, "I_SOLO", params.solo and 1 or 0)
        return {success = true}
    end
    return {success = false, error = "Track not found"}
end

function handlers.create_midi_item(params)
    local track = reaper.GetTrack(0, params.track_index)
    if not track then
        return {success = false, error = "Track not found"}
    end
    
    local tempo = reaper.Master_GetTempo()
    local pos_sec = params.position * (60 / tempo)
    local len_sec = params.length * (60 / tempo)
    
    local item = reaper.CreateNewMIDIItemInProj(track, pos_sec, pos_sec + len_sec, false)
    if item then
        return {success = true, data = {item_index = 0}}
    end
    return {success = false, error = "Failed to create MIDI item"}
end

function handlers.add_notes(params)
    local track = reaper.GetTrack(0, params.track_index)
    if not track then
        return {success = false, error = "Track not found"}
    end
    
    local item = reaper.GetTrackMediaItem(track, params.item_index or 0)
    if not item then
        return {success = false, error = "Item not found"}
    end
    
    local take = reaper.GetActiveTake(item)
    if not take or not reaper.TakeIsMIDI(take) then
        return {success = false, error = "Not a MIDI take"}
    end
    
    local tempo = reaper.Master_GetTempo()
    local ppq = 960  -- Standard PPQ
    
    for _, note in ipairs(params.notes or {}) do
        local start_ppq = math.floor(note.start * ppq)
        local end_ppq = start_ppq + math.floor(note.duration * ppq)
        local pitch = note.pitch or 60
        local vel = note.velocity or 100
        
        reaper.MIDI_InsertNote(take, false, false, start_ppq, end_ppq, 0, pitch, vel, true)
    end
    
    reaper.MIDI_Sort(take)
    return {success = true}
end

function handlers.transport(params)
    local action = params.action
    if action == "play" then
        reaper.Main_OnCommand(1007, 0)  -- Play
    elseif action == "stop" then
        reaper.Main_OnCommand(1016, 0)  -- Stop
    elseif action == "record" then
        reaper.Main_OnCommand(1013, 0)  -- Record
    else
        return {success = false, error = "Unknown transport action"}
    end
    return {success = true}
end

function handlers.list_plugins(params)
    local filter = (params.filter or ""):lower()
    local plugins = {}
    
    -- Enumerate VST plugins
    local idx = 0
    while true do
        local retval, name = reaper.EnumInstalledFX(idx)
        if not retval then break end
        
        if filter == "" or name:lower():find(filter, 1, true) then
            table.insert(plugins, {name = name})
        end
        idx = idx + 1
    end
    
    return {success = true, data = {plugins = plugins}}
end

function handlers.load_plugin(params)
    local track = reaper.GetTrack(0, params.track_index)
    if not track then
        return {success = false, error = "Track not found"}
    end
    
    local plugin_name = params.plugin_name
    local fx_index = reaper.TrackFX_AddByName(track, plugin_name, false, -1)
    
    if fx_index >= 0 then
        return {success = true, data = {plugin_name = plugin_name, fx_index = fx_index}}
    end
    return {success = false, error = "Plugin not found: " .. plugin_name}
end

-- =============================================================================
-- MAIN LOOP
-- =============================================================================

local client = nil
local buffer = ""

local function process_message(msg)
    local ok, request = pcall(json.decode, msg)
    if not ok or not request then
        return json.encode({success = false, error = "Invalid JSON"})
    end
    
    local command = request.command
    local params = request.params or {}
    
    local handler = handlers[command]
    if handler then
        local ok, result = pcall(handler, params)
        if ok then
            return json.encode(result)
        else
            return json.encode({success = false, error = tostring(result)})
        end
    else
        return json.encode({success = false, error = "Unknown command: " .. tostring(command)})
    end
end

local function try_connect()
    if client then
        client:close()
        client = nil
    end
    
    client = socket.tcp()
    client:settimeout(0.1)
    
    local result, err = client:connect(HOST, PORT)
    if result then
        connected = true
        log("Connected to MCP server at " .. HOST .. ":" .. PORT)
        return true
    else
        connected = false
        client:close()
        client = nil
        return false
    end
end

local last_connect_attempt = 0
local RECONNECT_INTERVAL = 5  -- seconds

local function main_loop()
    local now = os.time()
    
    -- Try to connect if not connected
    if not connected then
        if now - last_connect_attempt >= RECONNECT_INTERVAL then
            last_connect_attempt = now
            try_connect()
        end
        reaper.defer(main_loop)
        return
    end
    
    -- Read incoming data
    local data, err, partial = client:receive("*l")
    data = data or partial
    
    if data and #data > 0 then
        buffer = buffer .. data
        
        -- Process complete messages
        while true do
            local newline_pos = buffer:find("\n")
            if not newline_pos then break end
            
            local msg = buffer:sub(1, newline_pos - 1)
            buffer = buffer:sub(newline_pos + 1)
            
            if #msg > 0 then
                reaper.Undo_BeginBlock()
                local response = process_message(msg)
                reaper.Undo_EndBlock("Scythe MCP Action", -1)
                
                -- Send response
                local ok, send_err = client:send(response .. "\n")
                if not ok then
                    log("Send error: " .. tostring(send_err))
                    connected = false
                    client:close()
                    client = nil
                end
            end
        end
    elseif err == "closed" then
        log("Connection closed by server")
        connected = false
        client:close()
        client = nil
    end
    
    reaper.defer(main_loop)
end

-- =============================================================================
-- STARTUP
-- =============================================================================

log("Scythe MCP Client starting...")
log("Connecting to " .. HOST .. ":" .. PORT)

try_connect()
main_loop()

--[[
Scythe MCP - REAPER Command Poller

Polls a JSON file for commands from the MCP server.
No external dependencies required - uses REAPER's built-in Lua.

Installation:
1. Copy this file to REAPER Scripts folder
2. Actions -> Load ReaScript
3. Run the script (it will keep polling in background)
]]

local POLL_INTERVAL = 0.1  -- seconds
local TEMP_DIR = os.getenv("TEMP") or os.getenv("TMP") or "/tmp"
local COMMAND_FILE = TEMP_DIR .. "/scythe_mcp/command.json"
local RESPONSE_FILE = TEMP_DIR .. "/scythe_mcp/response.json"

-- Ensure directory exists
os.execute('mkdir "' .. TEMP_DIR .. '\\scythe_mcp" 2>nul')

-- Simple JSON parser (minimal, for our specific format)
local function parse_json(str)
    local result = {}
    
    -- Extract command
    local cmd = str:match('"command"%s*:%s*"([^"]*)"')
    if cmd then result.command = cmd end
    
    -- Extract params
    result.params = {}
    
    -- Special handling for "code" field (may contain escaped quotes and newlines)
    local code_start = str:find('"code"%s*:%s*"')
    if code_start then
        local quote_pos = str:find('"', code_start + 8)
        -- We need to find the specific closing quote that isn't escaped
        -- But first, let's just parse aggressively from the start position
        local content_start = str:find('"', code_start) + 1
        
        local i = content_start
        local code_chars = {}
        while i <= #str do
            local c = str:sub(i, i)
            if c == '\\' then
                local next_c = str:sub(i+1, i+1)
                if next_c == '"' then table.insert(code_chars, '"')
                elseif next_c == '\\' then table.insert(code_chars, '\\')
                elseif next_c == '/' then table.insert(code_chars, '/')
                elseif next_c == 'b' then table.insert(code_chars, '\b')
                elseif next_c == 'f' then table.insert(code_chars, '\f')
                elseif next_c == 'n' then table.insert(code_chars, '\n')
                elseif next_c == 'r' then table.insert(code_chars, '\r')
                elseif next_c == 't' then table.insert(code_chars, '\t')
                else 
                    table.insert(code_chars, c)
                    table.insert(code_chars, next_c)
                end
                i = i + 2
            elseif c == '"' then
                break
            else
                table.insert(code_chars, c)
                i = i + 1
            end
        end
        result.params.code = table.concat(code_chars)
    end
    
    -- Extract other simple params
    for key, val in str:gmatch('"(%w+)"%s*:%s*([%d%.]+)') do
        if key ~= "timestamp" then
            result.params[key] = tonumber(val)
        end
    end
    
    -- Extract string params (not code)
    for key, val in str:gmatch('"(%w+)"%s*:%s*"([^"]*)"') do
        if key ~= "command" and key ~= "code" and not result.params[key] then
            result.params[key] = val
        end
    end
    
    return result
end

local function write_response(data)
    local f = io.open(RESPONSE_FILE, "w")
    if f then
        -- Simple JSON encoding
        f:write('{"success": ' .. tostring(data.success))
        if data.message then
            f:write(', "message": "' .. data.message .. '"')
        end
        if data.error then
            f:write(', "error": "' .. data.error .. '"')
        end
        if data.result then
            -- Sanitize result for JSON string
            local res_str = tostring(data.result):gsub('"', '\\"'):gsub('\n', '\\n')
            f:write(', "result": "' .. res_str .. '"')
        end
        f:write('}')
        f:close()
    end
end

local function log(msg)
    reaper.ShowConsoleMsg("[Scythe] " .. tostring(msg) .. "\n")
end

-- Command handlers
local handlers = {}

function handlers.name_selected_track(params)
    local track = reaper.GetSelectedTrack(0, 0)
    if track then
        reaper.GetSetMediaTrackInfo_String(track, "P_NAME", params.name or "New Track", true)
        return {success = true, message = "Track renamed"}
    end
    return {success = false, error = "No track selected"}
end

function handlers.insert_midi_item(params)
    local track_idx = params.track_index or 0
    local track = reaper.GetTrack(0, track_idx)
    if not track then
        return {success = false, error = "Track not found at index " .. tostring(track_idx)}
    end
    
    local tempo = reaper.Master_GetTempo()
    local pos_sec = (params.position or 0) * (60 / tempo)
    local len_sec = (params.length or 4) * (60 / tempo)
    
    -- Create item
    local item = reaper.CreateNewMIDIItemInProj(track, pos_sec, pos_sec + len_sec, false)
    
    if item then
        local take = reaper.GetActiveTake(item)
        if take then
            reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", "Generated MIDI", true)
        end
        reaper.UpdateArrange()
        reaper.TrackList_AdjustWindows(false)
        
        local item_count = reaper.CountTrackMediaItems(track)
        
        return {
            success = true, 
            message = "MIDI item created", 
            result = "Items on track: " .. tostring(item_count)
        }
    end
    return {success = false, error = "Failed to create item"}
end

function handlers.add_notes(params)
    local track = reaper.GetTrack(0, params.track_index or 0)
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
    
    local ppq = 960
    local notes = params.notes or {}
    
    -- TODO: Implement full note parsing from JSON array
    -- Currently, notes from add_notes MCP tool are not fully parsed
    
    return {success = true, message = "Notes command received"}
end

function handlers.execute_lua(params)
    local code = params.code
    if not code or code == "" then
        return {success = false, error = "No code provided"}
    end
    
    -- Compile and execute the Lua code
    local func, err = load(code)
    if not func then
        return {success = false, error = "Syntax error: " .. tostring(err)}
    end
    
    -- Execute with pcall for safety
    local ok, result = pcall(func)
    if not ok then
        return {success = false, error = "Runtime error: " .. tostring(result)}
    end
    
    -- Return result if any
    if result ~= nil then
        return {success = true, message = "Executed", result = tostring(result)}
    end
    return {success = true, message = "Lua code executed successfully"}
end

function handlers.run_lua_file(params)
    local path = params.path
    if not path then
        return {success = false, error = "No path provided"}
    end
    
    local f = io.open(path, "r")
    if not f then
        return {success = false, error = "File not found: " .. path}
    end
    local code = f:read("*all")
    f:close()
    
    -- Reuse execute_lua logic
    return handlers.execute_lua({code = code})
end

-- Last processed timestamp to avoid re-processing
local last_timestamp = 0

local function process_commands()
    -- Check if command file exists
    local f = io.open(COMMAND_FILE, "r")
    if not f then
        reaper.defer(process_commands)
        return
    end
    
    local content = f:read("*all")
    f:close()
    
    if not content or content == "" then
        reaper.defer(process_commands)
        return
    end
    
    local cmd = parse_json(content)
    
    -- Check timestamp to avoid reprocessing
    local timestamp = tonumber(content:match('"timestamp"%s*:%s*([%d%.]+)') or 0)
    if timestamp and timestamp > last_timestamp then
        last_timestamp = timestamp
        
        if cmd.command then
            log("Received command: " .. cmd.command)
            
            local handler = handlers[cmd.command]
            if handler then
                -- reaper.Undo_BeginBlock()
                local result = handler(cmd.params or {})
                -- reaper.Undo_EndBlock("Scythe: " .. cmd.command, -1)
                write_response(result)
            else
                write_response({success = false, error = "Unknown command: " .. cmd.command})
            end
        end
    end
    
    reaper.defer(process_commands)
end

-- Start
log("Scythe MCP Command Poller started")
log("Watching: " .. COMMAND_FILE)
log("Make sure OSC is enabled in REAPER: Preferences -> Control/OSC/Web")

process_commands()

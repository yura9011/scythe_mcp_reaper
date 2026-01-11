import subprocess
import json
import os
import sys
import time
import threading
from queue import Queue, Empty

# Path to the server entry point or command
SERVER_CMD = ["uv", "run", "scythe-mcp"]
WORKING_DIR = r"d:\tareas\experiment_cubase"

def test_mcp_server():
    print(f"Starting MCP Server: {' '.join(SERVER_CMD)}")
    
    # Start the server process
    process = subprocess.Popen(
        SERVER_CMD,
        cwd=WORKING_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr, # Pipe stderr to console for debugging
        text=True,
        bufsize=1 # Line buffered
    )
    
    def read_output(proc, q):
        for line in iter(proc.stdout.readline, ''):
            q.put(line)
        proc.stdout.close()

    q = Queue()
    t = threading.Thread(target=read_output, args=(process, q))
    t.daemon = True
    t.start()
    
    def send_request(req):
        json_req = json.dumps(req)
        print(f"\n-> SEND: {json_req}")
        process.stdin.write(json_req + "\n")
        process.stdin.flush()

    def get_response(timeout=5):
        start = time.time()
        while time.time() - start < timeout:
            try:
                line = q.get(timeout=1)
                print(f"<- RECV: {line.strip()}")
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue # Ignore debug logs if any
            except Empty:
                continue
        return None

    try:
        # 1. Initialize
        print("\n--- STEP 1: INITIALIZE ---")
        send_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", # FastMCP version dependent, usually accepts recent
                "capabilities": {},
                "clientInfo": {"name": "TestClient", "version": "1.0"}
            }
        })
        
        # Read until initialization response
        # FastMCP might output logs first, so we loop
        init_response = get_response()
        while init_response and "result" not in init_response:
             init_response = get_response()
             
        assert init_response, "No response to initialize"
        print("Initialized!")
        
        # Send initialized notification
        send_request({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })

        # 2. List Tools
        print("\n--- STEP 2: LIST TOOLS ---")
        send_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        
        tools_response = get_response()
        while tools_response and tools_response.get("id") != 2:
             tools_response = get_response()
             
        assert tools_response, "No response to tools/list"
        tools = tools_response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        print(f"Available Tools: {tool_names}")
        
        assert "add_drum_track" in tool_names, "add_drum_track tool missing!"
        
        # 3. Call Tool (create_song_sketch)
        print("\n--- STEP 3: CALL TOOL (create_song_sketch) ---")
        send_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "create_song_sketch",
                "arguments": {
                    "genre": "trap",
                    "key": "D",
                    "scale_type": "phrygian",
                    "bars": 4
                }
            }
        })
        
        tool_res = get_response(timeout=30) # Allow time for multiple track creations
        while tool_res and tool_res.get("id") != 3:
             tool_res = get_response(timeout=10)
        
        assert tool_res, "No response to tools/call"
        if "error" in tool_res:
             print(f"Tool Error: {tool_res['error']}")
        else:
             print(f"Tool Result: {tool_res['result']}")
             
    finally:
        print("\nClosing server...")
        try:
            process.terminate()
            process.wait(timeout=2)
        except:
            process.kill()

if __name__ == "__main__":
    test_mcp_server()

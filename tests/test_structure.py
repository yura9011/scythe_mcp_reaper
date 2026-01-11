import importlib
import pytest
from scythe_mcp.server.main import mcp

def test_imports():
    """Verify core modules can be imported."""
    modules = [
        "scythe_mcp.server.main",
        "scythe_mcp.server.reaper_bridge",
        "scythe_mcp.generators.drums",
        "scythe_mcp.generators.basslines",
        "scythe_mcp.generators.melodies",
        "scythe_mcp.music_theory.scales",
        "scythe_mcp.music_theory.chords",
        "scythe_mcp.music_theory.progressions",
        "scythe_mcp.music_theory.rhythm",
    ]
    
    for module in modules:
        importlib.import_module(module)

def test_server_instantiation():
    """Verify MCP server instance is created."""
    assert mcp is not None
    assert mcp.name == "ScytheMCP"

def test_generators_exist():
    """Verify generator functions exist."""
    from scythe_mcp.generators.drums import generate_drum_pattern
    assert callable(generate_drum_pattern)

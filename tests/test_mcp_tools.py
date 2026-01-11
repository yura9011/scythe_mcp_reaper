import json
import pytest
from scythe_mcp.server.main import generate_drums_json, generate_bass_json, generate_melody_json, mcp

# Mock context
class MockContext:
    pass

ctx = MockContext()

def test_generate_drums_json():
    """Test generating drums JSON."""
    result = generate_drums_json(ctx, genre="electronic", bars=4)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "pitch" in data[0]

def test_generate_bass_json():
    """Test generating bass JSON."""
    result = generate_bass_json(ctx, progression=["Cmaj7", "G7"], style="walking")
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) > 0

def test_generate_melody_json():
    """Test generating melody JSON."""
    result = generate_melody_json(ctx, key="D", scale_type="minor")
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) > 0

"""
Scythe MCP - REAPER Integration Server
"""

__version__ = "0.1.0"

def get_mcp():
    """Get the MCP server instance."""
    from .main import mcp
    return mcp

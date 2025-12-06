#!/usr/bin/env python3
"""
RADKit MCP Server - Backward Compatibility Wrapper

This file maintains backward compatibility with existing installations.
All functionality has been moved to src/radkit_mcp/ for better modularity.

For new installations, you can use:
- python -m radkit_mcp.server
- fastmcp run src/radkit_mcp/server.py

But this wrapper ensures existing Claude Desktop configs and scripts
continue to work without modification.
"""

# Import from new modular structure
from src.radkit_mcp.server import mcp, main

# Re-export for backward compatibility
__all__ = ["mcp", "main"]

if __name__ == "__main__":
    main()

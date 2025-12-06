"""
RADKit MCP Server - Modular Architecture

A professional FastMCP server implementation for Cisco RADKit, providing MCP tools
for network device management via SNMP, command execution, and inventory discovery.

This package provides:
- Certificate and environment variable authentication
- SNMP operations
- Command execution with timeout and truncation
- Device inventory discovery
- Service management and caching
"""

__version__ = "2.0.0"
__author__ = "Cisco DevNet & Contributors"

from .server import mcp

__all__ = ["mcp"]

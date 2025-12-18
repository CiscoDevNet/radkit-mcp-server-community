"""
MCP Tool Registration Module

This module contains functions for registering FastMCP tools.
Each submodule provides a registration function that takes the mcp instance
and registers the appropriate tools.
"""

from .exec_tools import register_exec_tools
from .snmp_tools import register_snmp_tools

__all__ = ["register_exec_tools", "register_snmp_tools"]

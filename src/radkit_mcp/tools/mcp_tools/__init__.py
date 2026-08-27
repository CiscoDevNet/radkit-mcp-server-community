"""
MCP Tool Registration Module

This module contains functions for registering FastMCP tools.
Each submodule provides a registration function that takes the mcp instance
and registers the appropriate tools.
"""

from .exec_tools import register_exec_tools
from .port_forwarding_tools import register_port_forwarding_tools
from .scp_tools import register_scp_tools
from .snmp_tools import register_snmp_tools

__all__ = ["register_exec_tools", "register_port_forwarding_tools", "register_scp_tools", "register_snmp_tools"]

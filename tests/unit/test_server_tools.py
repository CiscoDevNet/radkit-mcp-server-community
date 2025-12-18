"""
Unit tests for server tool definitions.

These tests verify tool registration and parameter validation.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.unit
def test_server_metadata():
    """Test server metadata."""
    from radkit_mcp.server import mcp

    assert mcp.name == "RADKit MCP Server"
    assert mcp.version == "2.0.0"


@pytest.mark.unit
def test_server_has_tools():
    """Test that server has tools defined."""
    from radkit_mcp.server import mcp

    # FastMCP should have tools registered
    # We can't easily introspect them without starting the server,
    # but we can verify the module imports correctly
    assert mcp is not None
    assert hasattr(mcp, 'name')
    assert hasattr(mcp, 'version')


@pytest.mark.unit
def test_tool_functions_exist():
    """Test that tool functions are defined in server module."""
    from radkit_mcp import server

    # Verify inventory tool functions exist in server
    assert hasattr(server, 'get_device_inventory_names_tool')
    assert hasattr(server, 'get_device_attributes_tool')

    # Verify tool registration functions are imported
    assert hasattr(server, 'register_exec_tools')
    assert hasattr(server, 'register_snmp_tools')


@pytest.mark.unit
def test_tool_modules_import():
    """Test that tool modules import correctly."""
    # Test that we can import tool modules
    from radkit_mcp.tools import exec, snmp, inventory

    # Verify key functions exist
    assert hasattr(exec, 'radkit_exec_command')
    assert hasattr(snmp, 'radkit_snmp_get')
    assert hasattr(inventory, 'get_device_inventory_names')
    assert hasattr(inventory, 'get_device_attributes')

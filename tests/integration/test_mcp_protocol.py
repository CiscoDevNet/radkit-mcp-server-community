"""
MCP Protocol integration tests for RADKit FastMCP server.

These tests use FastMCP's in-memory client to test the server
from an MCP protocol perspective with real devices.

Requires RADKIT_TEST_DEVICE to be set in environment.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from fastmcp import Client

# Load environment variables
load_dotenv()

# Import the FastMCP server instance
from radkit_mcp.server import mcp


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available MCP tools."""
    async with Client(mcp) as client:
        tools = await client.list_tools()

        # Verify we have the expected tools
        tool_names = [tool.name for tool in tools]
        assert "snmp_get" in tool_names
        assert "exec_command" in tool_names
        assert "get_device_inventory_names_tool" in tool_names
        assert "get_device_attributes_tool" in tool_names

        # Verify tool details
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_snmp_get_single_oid(test_device_name, test_snmp_oid):
    """Test SNMP GET with a single OID via MCP client."""
    async with Client(mcp) as client:
        call_result = await client.call_tool("snmp_get", {
            "device_name": test_device_name,
            "oid": test_snmp_oid,
            "timeout": 10.0
        })

        result = call_result.structured_content['result']

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        first_result = result[0]
        assert first_result["device_name"] == test_device_name
        assert first_result["oid"] == test_snmp_oid
        assert "value" in first_result
        assert "type" in first_result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_snmp_get_multiple_oids(test_device_name):
    """Test SNMP GET with multiple OIDs via MCP client."""
    async with Client(mcp) as client:
        oids = [
            "1.3.6.1.2.1.1.1.0",  # sysDescr
            "1.3.6.1.2.1.1.3.0",  # sysUpTime
        ]

        call_result = await client.call_tool("snmp_get", {
            "device_name": test_device_name,
            "oid": oids,
            "timeout": 10.0
        })

        result = call_result.structured_content['result']

        assert isinstance(result, list)
        assert len(result) >= 2

        result_oids = [r["oid"] for r in result]
        for oid in oids:
            assert oid in result_oids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exec_command_single(test_device_name, test_command):
    """Test executing a single command via MCP client."""
    async with Client(mcp) as client:
        call_result = await client.call_tool("exec_command", {
            "device_name": test_device_name,
            "command": test_command
        })

        result = call_result.structured_content['result']

        assert result is not None
        assert isinstance(result, dict)
        assert result["device_name"] == test_device_name
        assert result["command"] == test_command
        assert result["status"] == "SUCCESS"
        assert "output" in result
        assert len(result["output"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exec_command_multiple(test_device_name):
    """Test executing multiple commands via MCP client."""
    async with Client(mcp) as client:
        commands = ["show clock", "show version | include Version"]

        call_result = await client.call_tool("exec_command", {
            "device_name": test_device_name,
            "command": commands
        })

        result = call_result.structured_content['result']

        assert isinstance(result, list)
        assert len(result) == len(commands)

        for i, cmd_result in enumerate(result):
            assert cmd_result["device_name"] == test_device_name
            assert cmd_result["command"] == commands[i]
            assert cmd_result["status"] == "SUCCESS"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exec_command_with_timeout(test_device_name, test_command):
    """Test command execution with custom timeout."""
    async with Client(mcp) as client:
        call_result = await client.call_tool("exec_command", {
            "device_name": test_device_name,
            "command": test_command,
            "timeout": 30
        })

        result = call_result.structured_content['result']

        assert result["status"] == "SUCCESS"
        assert result["device_name"] == test_device_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_snmp_get_with_service_override(test_device_name):
    """Test SNMP GET with service serial override."""
    default_service = os.getenv("RADKIT_DEFAULT_SERVICE_SERIAL")

    if not default_service:
        pytest.skip("RADKIT_DEFAULT_SERVICE_SERIAL not set")

    async with Client(mcp) as client:
        call_result = await client.call_tool("snmp_get", {
            "device_name": test_device_name,
            "oid": "1.3.6.1.2.1.1.1.0",
            "service_serial": default_service
        })

        result = call_result.structured_content['result']

        assert result is not None
        assert len(result) > 0
        assert result[0]["device_name"] == test_device_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_device_name():
    """Test error handling for invalid device name."""
    async with Client(mcp) as client:
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("snmp_get", {
                "device_name": "nonexistent-device-12345",
                "oid": "1.3.6.1.2.1.1.1.0"
            })

        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "device" in error_msg


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_metadata():
    """Test server metadata and capabilities."""
    async with Client(mcp) as client:
        tools = await client.list_tools()

        assert len(tools) > 0

        for tool in tools:
            assert tool.inputSchema is not None
            assert "properties" in tool.inputSchema

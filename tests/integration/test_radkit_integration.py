"""
Integration tests for RADKit FastMCP server.

These tests require real devices and RADKit service credentials.
Set RADKIT_TEST_DEVICE in your .env file to specify the device to test.

Example .env:
    RADKIT_TEST_DEVICE=router1
    RADKIT_TEST_SNMP_OID=1.3.6.1.2.1.1.1.0
    RADKIT_TEST_COMMAND=show clock
"""

import os
import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from radkit_client.sync import Client

# Load environment variables
load_dotenv()


@pytest.mark.integration
def test_authentication():
    """Test RADKit certificate authentication."""
    from radkit_mcp import client as radkit_client_module

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)
            # If we get here, authentication succeeded
            assert True
    finally:
        radkit_client_module.cleanup_cert_files()


@pytest.mark.integration
async def test_snmp_get(test_device_name, test_snmp_oid):
    """Test SNMP GET functionality with real device."""
    from radkit_mcp import client as radkit_client_module
    from radkit_mcp.tools.snmp import radkit_snmp_get

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)

            # Test SNMP GET
            result = await radkit_snmp_get(test_device_name, test_snmp_oid)

            # Validate response
            assert isinstance(result, list), "Result should be a list"
            assert len(result) > 0, "Result should contain at least one entry"

            first_result = result[0]
            assert first_result["device_name"] == test_device_name
            assert first_result["oid"] == test_snmp_oid
            assert "value" in first_result
            assert "type" in first_result

    finally:
        radkit_client_module.cleanup_cert_files()


@pytest.mark.integration
async def test_exec_command(test_device_name, test_command):
    """Test command execution functionality with real device."""
    from radkit_mcp import client as radkit_client_module
    from radkit_mcp.tools.exec import radkit_exec_command

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)

            # Test command execution
            result = await radkit_exec_command(test_device_name, test_command)

            # Validate response
            assert isinstance(result, dict), "Result should be a dictionary"
            assert result["device_name"] == test_device_name
            assert result["command"] == test_command
            assert result["status"] == "SUCCESS"
            assert "output" in result
            assert len(result["output"]) > 0

    finally:
        radkit_client_module.cleanup_cert_files()


@pytest.mark.integration
async def test_snmp_get_multiple_oids(test_device_name):
    """Test SNMP GET with multiple OIDs."""
    from radkit_mcp import client as radkit_client_module
    from radkit_mcp.tools.snmp import radkit_snmp_get

    oids = [
        "1.3.6.1.2.1.1.1.0",  # sysDescr
        "1.3.6.1.2.1.1.3.0",  # sysUpTime
    ]

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)

            result = await radkit_snmp_get(test_device_name, oids)

            # Validate response
            assert isinstance(result, list)
            assert len(result) >= 2, "Should have results for both OIDs"

            result_oids = [r["oid"] for r in result]
            for oid in oids:
                assert oid in result_oids, f"OID {oid} should be in results"

    finally:
        radkit_client_module.cleanup_cert_files()


@pytest.mark.integration
async def test_exec_command_multiple(test_device_name):
    """Test executing multiple commands."""
    from radkit_mcp import client as radkit_client_module
    from radkit_mcp.tools.exec import radkit_exec_command

    commands = ["show clock", "show version | include Version"]

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)

            result = await radkit_exec_command(test_device_name, commands)

            # For multiple commands, result should be a list
            assert isinstance(result, list)
            assert len(result) == len(commands)

            for i, cmd_result in enumerate(result):
                assert cmd_result["device_name"] == test_device_name
                assert cmd_result["command"] == commands[i]
                assert cmd_result["status"] == "SUCCESS"

    finally:
        radkit_client_module.cleanup_cert_files()


@pytest.mark.integration
async def test_inventory_operations(test_device_name):
    """Test inventory discovery and attribute retrieval."""
    from radkit_mcp import client as radkit_client_module
    from radkit_mcp.tools.inventory import get_device_inventory_names, get_device_attributes

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)

            # Test inventory names
            inventory = await get_device_inventory_names()
            assert isinstance(inventory, str)
            assert test_device_name in inventory

            # Test device attributes
            attributes = await get_device_attributes(test_device_name)
            assert isinstance(attributes, str)
            assert test_device_name in attributes

    finally:
        radkit_client_module.cleanup_cert_files()

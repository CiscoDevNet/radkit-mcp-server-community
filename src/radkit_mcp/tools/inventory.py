"""
Inventory operations tool for RADKit.

This module provides MCP tools for discovering and querying network devices
in the RADKit inventory.
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Handle imports for both module and standalone execution
try:
    from ..client import get_service
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from client import get_service


async def get_device_inventory_names(service_serial: Optional[str] = None) -> str:
    """
    Returns a string with the names of the devices onboarded in the Cisco RADKit service's inventory.

    Use this first when the user asks about "devices", "network", or "all devices".

    Args:
        service_serial: Optional service serial to override default

    Returns:
        str: List of devices onboarded in the Cisco RADKit service's inventory
             [ex. {"p0-2e", "p1-2e"}]

    Raises:
        Exception: If there's an error fetching the inventory
    """
    try:
        # Get service (synchronous operation)
        service = get_service(service_serial)

        # Run inventory fetch in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        inventory_values = await loop.run_in_executor(
            None,
            lambda: service.inventory.values()
        )

        # Return device names as a set string
        return str({device.name for device in inventory_values})

    except Exception as ex:
        error_msg = f"⚠️ Error fetching device inventory: {str(ex)}"
        raise Exception(error_msg)


async def get_device_attributes(
    target_device: str,
    service_serial: Optional[str] = None
) -> str:
    """
    Returns a JSON string with the attributes of the specified target device.

    Always try this first when the user asks about a specific device.

    This tool is safe to call in parallel for multiple devices. When querying multiple devices,
    you should call this tool concurrently for all devices to improve performance.

    Args:
        target_device: Target device to get the attributes from.
        service_serial: Optional service serial to override default

    Returns:
        str: JSON string with the following information:
        {
            "name": (str) Name of the device as onboarded in the inventory
            "host": (str) IP address of the device
            "device_type": (str) Platform or Device Type
            "description": (str) Description of the device
            "terminal_config": (bool) The device's terminal is enabled for configurations
            "netconf_config": (bool) The device is enabled with NETCONF
            "snmp_version": (str) The device is enabled with SNMP
            "swagger_config": (bool) The device has a Swagger definition
            "http_config": (bool) The device is enabled with HTTP
            "forwarded_tcp_ports": [str] The device has forwarded TCP ports
            "terminal_capabilities": [str] Enlists the capabilities of the device's terminal
        }

        Example:
        {
            "name": "p0-2e",
            "host": "10.48.172.59",
            "device_type": "IOS_XE",
            "description": "",
            "terminal_config": true,
            "netconf_config": false,
            "snmp_version": "v2c",
            "swagger_config": false,
            "http_config": false,
            "forwarded_tcp_ports": "",
            "terminal_capabilities": [
                "DOWNLOAD",
                "INTERACTIVE",
                "EXEC",
                "UPLOAD"
            ]
        }

    Raises:
        Exception: If there's an error fetching the device's information or device not found
    """
    try:
        inventory_dict = {"name": target_device}

        # Get service (synchronous operation)
        service = get_service(service_serial)

        # Run device attribute fetch in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()

        def fetch_attributes():
            try:
                device_attributes = service.inventory[target_device].attributes.internal
                return device_attributes
            except KeyError:
                raise ValueError(f"Device '{target_device}' not found in RADKit inventory")

        device_attributes = await loop.run_in_executor(None, fetch_attributes)

        # Merge attributes into response dict
        for key in device_attributes.keys():
            inventory_dict[key] = device_attributes[key]

        return json.dumps(inventory_dict, indent=2)

    except ValueError as ve:
        # Re-raise ValueError for device not found
        raise ve
    except Exception as ex:
        error_msg = f"⚠️ Error fetching device attributes for {target_device}: {str(ex)}"
        raise Exception(error_msg)

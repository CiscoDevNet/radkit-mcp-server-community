"""
SNMP operations tool for RADKit.

This module provides MCP tools for performing SNMP operations
on network devices via RADKit.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Union

# Handle imports for both module and standalone execution
try:
    from ..client import get_service
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from client import get_service


async def radkit_snmp_get(
    device_name: str,
    oid: Union[str, list[str]],
    service_serial: Optional[str] = None,
    timeout: Optional[float] = 10.0
) -> list[dict]:
    """
    Perform SNMP GET operation on a RADKit-managed device.

    This tool retrieves SNMP values for one or more Object Identifiers (OIDs)
    from a network device managed by RADKit.

    Args:
        device_name: Name of the device in RADKit inventory (e.g., "router1")
        oid: Single OID string or list of OID strings (e.g., "1.3.6.1.2.1.1.1.0" or
             ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"])
        service_serial: Optional service serial to override default. If not provided,
                       uses RADKIT_DEFAULT_SERVICE_SERIAL from environment.
        timeout: Request timeout in seconds (default: 10.0)

    Returns:
        List of dictionaries containing SNMP results:
        [
            {
                "device_name": "device-name",
                "oid": "1.3.6.1.2.1.1.1.0",
                "value": "Cisco IOS Software...",
                "type": "OctetString"
            },
            ...
        ]

    Raises:
        ValueError: If device not found in inventory
        Exception: If SNMP operation fails

    Examples:
        # Get single OID
        result = radkit_snmp_get("router1", "1.3.6.1.2.1.1.1.0")

        # Get multiple OIDs
        result = radkit_snmp_get(
            "router1",
            ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"]
        )

        # Use different service
        result = radkit_snmp_get(
            "router1",
            "1.3.6.1.2.1.1.1.0",
            service_serial="other-service"
        )
    """
    try:
        # Handle None value for optional parameter
        timeout = timeout if timeout is not None else 10.0

        # Get the appropriate service (synchronous operation)
        service = get_service(service_serial)

        # Normalize OID to list for consistent handling
        # RADKit SNMP API accepts either:
        # - Single OID: device.snmp.get("1.3.6.1.2.1.1.1.0")
        # - List of OIDs: device.snmp.get(["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"])
        oids_param = oid if isinstance(oid, (list, tuple)) else oid
        if isinstance(oid, list) and not oid:
            raise ValueError("At least one OID must be provided")

        # Run SNMP GET in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()

        def perform_snmp_get():
            # Get device inventory by name
            inventory = service.inventory.filter("name", device_name)
            if not inventory:
                raise ValueError(f"Device '{device_name}' not found in RADKit inventory")

            # Get device from inventory
            device = inventory[device_name]

            # Execute SNMP GET operation
            # Pass OIDs as-is (single OID or list of OIDs)
            # Timeout is handled by .wait() method
            if timeout and timeout > 0:
                snmp_result = device.snmp.get(oids_param).wait(timeout).result
            else:
                snmp_result = device.snmp.get(oids_param).wait().result

            # Format results
            # The result is an SNMPTable indexed by row number
            results = []
            for i in range(len(snmp_result)):
                row = snmp_result[i]

                # Check if row has an error
                if hasattr(row, '__str__') and 'ERROR:' in str(row):
                    # Skip error rows or include them with error info
                    result_entry = {
                        "device_name": device_name,
                        "oid": getattr(row, 'oid_str', ''),
                        "value": str(row),
                        "type": "ERROR",
                        "error": True
                    }
                else:
                    result_entry = {
                        "device_name": device_name,
                        "oid": row.oid_str,
                        "value": row.value,
                        "type": row.type,
                        "error": False
                    }
                results.append(result_entry)

            # Filter out errors by default
            results = [r for r in results if not r.get("error", False)]

            if not results:
                raise Exception(
                    f"SNMP GET returned no valid results for device {device_name}. "
                    "This may indicate an SNMP configuration issue or RADKit service error."
                )

            return results

        return await loop.run_in_executor(None, perform_snmp_get)

    except ValueError as ve:
        # Re-raise ValueError for device not found or invalid OID
        raise ve
    except Exception as e:
        raise Exception(
            f"SNMP GET failed on device {device_name}: {e}"
        ) from e

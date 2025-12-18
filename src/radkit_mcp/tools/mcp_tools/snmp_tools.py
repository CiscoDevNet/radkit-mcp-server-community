"""
MCP SNMP Tool Registration

This module contains functions for registering SNMP tools with FastMCP.
"""

from typing import Union, Optional

# Handle imports for both module and standalone execution
try:
    from ..snmp import radkit_snmp_get
except ImportError:
    from tools.snmp import radkit_snmp_get


def register_snmp_tools(mcp):
    """
    Register SNMP tools with the FastMCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def snmp_get(
        device_name: str,
        oid: Union[str, list[str]],
        service_serial: Optional[str] = None,
        timeout: Optional[float] = 10.0
    ) -> list[dict]:
        """
        Perform SNMP GET operation on a RADKit-managed device

        Retrieves SNMP values for one or more Object Identifiers (OIDs) from a
        network device managed by RADKit.

        Args:
            device_name: Name of the device in RADKit inventory (e.g., "router1")
            oid: Single OID string or list of OID strings (e.g., "1.3.6.1.2.1.1.1.0")
            service_serial: Optional service serial to override default
            timeout: Request timeout in seconds (default: 10.0)

        Returns:
            List of dictionaries containing SNMP results with device_name, oid, value, and type

        Examples:
            # Get system description
            snmp_get(device_name="router1", oid="1.3.6.1.2.1.1.1.0")

            # Get multiple OIDs
            snmp_get(device_name="router1", oid=[
                "1.3.6.1.2.1.1.1.0",  # sysDescr
                "1.3.6.1.2.1.1.3.0"   # sysUpTime
            ])
        """
        # Handle None value for optional parameter
        timeout = timeout if timeout is not None else 10.0

        return await radkit_snmp_get(device_name, oid, service_serial, timeout)

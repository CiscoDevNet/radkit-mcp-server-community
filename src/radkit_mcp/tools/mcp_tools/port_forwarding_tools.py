"""MCP TCP port-forwarding tool registration."""

import asyncio
from typing import Optional

try:
    from ...client import get_service
except ImportError:
    from client import get_service


def register_port_forwarding_tools(mcp):
    """Register the TCP port-forwarding tool with the FastMCP server."""

    @mcp.tool()
    async def forward_tcp_port(
        device_name: str,
        local_port: int,
        destination_port: int,
        service_serial: Optional[str] = None,
    ) -> dict:
        """Forward a localhost TCP port to a RADKit-managed device.

        The destination port must be allowed in the device's RADKit Service
        configuration. The unauthenticated local listener is deliberately bound
        to localhost and remains active until the MCP server shuts down.

        Args:
            device_name: Name of the device in the RADKit inventory.
            local_port: Localhost port to listen on (1-65535).
            destination_port: TCP port on the target device (1-65535).
            service_serial: Optional service serial overriding the default.

        Returns:
            Forwarding status and local/destination connection details.
        """
        for name, port in (("local_port", local_port), ("destination_port", destination_port)):
            if isinstance(port, bool) or not 1 <= port <= 65535:
                raise ValueError(f"{name} must be an integer between 1 and 65535")

        def start_forwarder():
            service = get_service(service_serial)
            try:
                device = service.inventory[device_name]
            except KeyError as error:
                raise ValueError(f"Device '{device_name}' not found in RADKit inventory") from error

            forwarder = device.forward_tcp_port(
                local_port=local_port,
                destination_port=destination_port,
                local_address="localhost",
            )
            return {
                "device_name": device_name,
                "local_address": "localhost",
                "local_port": forwarder.local_port,
                "destination_port": forwarder.destination_port,
                "status": forwarder.status.value,
            }

        return await asyncio.to_thread(start_forwarder)

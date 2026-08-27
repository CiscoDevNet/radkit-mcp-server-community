"""
FastMCP server for Cisco RADKit

This module provides a FastMCP server with tools for interacting with
Cisco RADKit-managed network devices via SNMP, command execution, and
inventory discovery.

Supports dual-mode authentication:
- Environment variables (RADKIT_CERT_B64, etc.) for containers
- Local certificate files (~/.radkit/) for local development
- Certificate login (RADKIT_SERVICE_USERNAME) for interactive use
"""

from contextlib import asynccontextmanager
import ipaddress
import os
import sys
import logging
from pathlib import Path
from typing import Union, Optional
from dotenv import load_dotenv

from fastmcp import FastMCP
from radkit_client.sync import Client

# Handle imports for both module and standalone execution
try:
    from . import client as radkit_client_module
    from .settings import get_settings
    from .tools.inventory import get_device_inventory_names, get_device_attributes
    from .tools.mcp_tools import register_exec_tools, register_port_forwarding_tools, register_snmp_tools
except ImportError:
    # Running as standalone script - add parent to path
    sys.path.insert(0, str(Path(__file__).parent))
    import client as radkit_client_module
    from settings import get_settings
    from tools.inventory import get_device_inventory_names, get_device_attributes
    from tools.mcp_tools import register_exec_tools, register_port_forwarding_tools, register_snmp_tools


# Load environment variables from .env file if present
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """
    Manage RADKit client lifecycle.

    This lifespan handler creates a RADKit client context that persists
    for the duration of the FastMCP server. The client is authenticated
    using one of three methods (auto-detected):
    1. Base64 environment variables (for containers)
    2. Local certificate directory (for local development)
    3. Certificate login with username (for interactive use)
    """
    logger.info("=" * 60)
    logger.info("RADKit MCP Server - Starting up")
    logger.info("=" * 60)

    # Create RADKit client context
    with Client.create() as client:
        try:
            # Initialize RADKit client (auto-detects auth method)
            radkit_client_module.initialize_radkit_client(client)

            logger.info("=" * 60)
            logger.info("RADKit MCP Server - Ready")
            logger.info("=" * 60)

            # Yield control to FastMCP
            yield

        except Exception as e:
            logger.error(f"Error during RADKit client initialization: {e}")
            raise
        finally:
            logger.info("\nShutting down RADKit MCP Server...")
            # Cleanup temporary certificate files (if any)
            radkit_client_module.cleanup_cert_files()
            logger.info("✓ Shutdown complete")


# Create FastMCP server with lifespan handler
mcp = FastMCP(
    name="RADKit MCP Server",
    version="2.0.0",
    lifespan=lifespan
)

# Register MCP tools
register_exec_tools(mcp)
register_port_forwarding_tools(mcp)
register_snmp_tools(mcp)


# ============================================================================
# INVENTORY TOOLS
# ============================================================================

@mcp.tool()
async def get_device_inventory_names_tool() -> str:
    """
    Returns a string with the names of the devices onboarded in the Cisco RADKit service's inventory.
    Use this first when the user asks about "devices", "network", or "all devices".

    Returns:
        str: List of devices onboarded in the Cisco RADKit service's inventory
             [ex. {"p0-2e", "p1-2e"}]
    """
    return await get_device_inventory_names()


@mcp.tool()
async def get_device_attributes_tool(target_device: str) -> str:
    """
    Returns a JSON string with the attributes of the specified target device.
    Always try this first when the user asks about a specific device.

    This tool is safe to call in parallel for multiple devices. When querying multiple devices,
    you should call this tool concurrently for all devices to improve performance.

    Args:
        target_device: (str) Target device to get the attributes from.

    Returns:
        str: JSON string with device attributes including name, host, type, configs,
             SNMP/NETCONF status, capabilities, etc.
    """
    return await get_device_attributes(target_device)


def main():
    """Run the FastMCP server."""
    settings = get_settings()
    transport = settings.mcp_transport.lower()

    logger.info(f'✅ RADKit MCP Server starting with transport: {transport.upper()}')

    if transport in ("sse", "http"):
        host = settings.mcp_host
        port = settings.mcp_port

        # Security validation for network transports
        try:
            is_localhost = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_localhost = host.rstrip(".").lower() == "localhost"

        if not is_localhost:
            if not settings.allow_insecure_network_bind:
                logger.error(
                    f"Refusing to start: MCP_HOST={host} binds to a non-loopback address, "
                    "exposing unauthenticated tool access (including exec with sudo) to the network. "
                    "Set MCP_ALLOW_INSECURE_NETWORK_BIND=true to override if you are in an "
                    "isolated/trusted environment (e.g. a container with a host-side loopback publish)."
                )
                sys.exit(1)
            logger.warning("\n" + "="*70)
            logger.warning("⚠️  SECURITY WARNING: NON-LOCALHOST BINDING DETECTED")
            logger.warning("="*70)
            logger.warning(f"MCP server is binding to {host}:{port} (not localhost)")
            logger.warning("This exposes ALL MCP tools (including device CLI execution) to the network")
            logger.warning("without authentication. This is a HIGH SECURITY RISK.")
            logger.warning("MCP_ALLOW_INSECURE_NETWORK_BIND=true is set — proceeding as operator override.")
            logger.warning("Ensure network isolation (firewall rules, host-loopback publish, NetworkPolicy)")
            logger.warning("is in place to restrict access to this port.")
            logger.warning("="*70 + "\n")

        logger.info(f"Starting MCP server with {transport.upper()} transport on {host}:{port}")
        mcp.run(transport=transport, host=host, port=port)
    else:
        logger.info("Starting MCP server with STDIO transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

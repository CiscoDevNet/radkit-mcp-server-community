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
    from .tools.mcp_tools import register_exec_tools, register_snmp_tools
except ImportError:
    # Running as standalone script - add parent to path
    sys.path.insert(0, str(Path(__file__).parent))
    import client as radkit_client_module
    from settings import get_settings
    from tools.inventory import get_device_inventory_names, get_device_attributes
    from tools.mcp_tools import register_exec_tools, register_snmp_tools


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

    if transport == "https" or transport == "sse":
        host = settings.mcp_host
        port = settings.mcp_port

        logger.info(f"Starting MCP server with {transport.upper()} transport on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        logger.info("Starting MCP server with STDIO transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

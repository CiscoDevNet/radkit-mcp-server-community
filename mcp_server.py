import os
import json
import logging
import asyncio
from fastmcp import FastMCP
from dotenv import load_dotenv
from radkit_client.sync import Client, Service


load_dotenv()
mcp = FastMCP(name="RADKitMCP")

transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class RADKitServiceManager:
    """
    Manages a single RADKit service connection throughout the application lifecycle.
    """
    _instance = None
    _client_context = None
    _client = None
    _service_handler = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RADKitServiceManager, cls).__new__(cls)
        return cls._instance
    
    async def get_service_handler(self) -> Service:
        """
        Returns the RADKit service handler, creating it if it doesn't exist.
        Thread-safe with async lock.
        
        Returns:
            Service: The RADKit service handler instance
            
        Raises:
            Exception: If there's an error creating the connection
        """
        async with self._lock:
            if self._service_handler is None:
                try:
                    logger.info(f"🔌 Creating new RADKit connection for {os.getenv('RADKIT_SERVICE_USERNAME')}-{os.getenv('RADKIT_SERVICE_CODE')}")
                    # Run blocking operations in executor to avoid blocking event loop
                    loop = asyncio.get_event_loop()
                    
                    def create_connection():
                        client_context = Client.create()
                        client_instance = client_context.__enter__()
                        radkit_service_client = client_instance.certificate_login(os.getenv("RADKIT_SERVICE_USERNAME"))
                        service_handler = radkit_service_client.service(os.getenv("RADKIT_SERVICE_CODE")).wait()
                        return client_context, service_handler
                    
                    self._client_context, self._service_handler = await loop.run_in_executor(None, create_connection)
                    logger.info("✅ RADKit connection established successfully")
                except Exception as ex:
                    logger.error(f"⚠️ Error creating RADKit connection: {str(ex)}")
                    raise
        
        return self._service_handler
    
    async def close(self):
        """
        Closes the RADKit connection if it exists.
        """
        async with self._lock:
            if self._client_context is not None:
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        self._client_context.__exit__, 
                        None, None, None
                    )
                    logger.info("🔌 RADKit connection closed")
                except Exception as ex:
                    logger.error(f"⚠️ Error closing RADKit connection: {str(ex)}")
                finally:
                    self._client_context = None
                    self._service_handler = None


# Create a global service manager instance
radkit_service_manager = RADKitServiceManager()


async def _get_radkit_service_handler() -> Service:
    """
    Returns the RADKit service handler.
    
    Returns:
        Service: The RADKit service handler instance
        
    Raises:
        Exception: If there's an error getting the connection
    """
    try:
        return await radkit_service_manager.get_service_handler()
    except Exception as ex:
        error_msg = f"⚠️ Error: {str(ex)}"
        logger.error(error_msg)
        raise Exception(error_msg)


@mcp.tool()
async def get_device_inventory_names(toolCallId: str = None) -> str:
    """Returns a string with the names of the devices onboarded in the Cisco RADKit service's inventory.
    Use this first when the user asks about "devices", "network", or "all devices".

    Returns:
        str: List of devices onboarded in the Cisco RADKit service's inventory [ex. {"p0-2e", ""p1-2e"}]
    """
    radkit_service_handler = await _get_radkit_service_handler()
    loop = asyncio.get_event_loop()
    inventory_values = await loop.run_in_executor(
        None, 
        lambda: radkit_service_handler.inventory.values()
    )
    return str({ device.name for device in inventory_values })


@mcp.tool()
async def get_device_attributes(target_device:str, toolCallId: str = None) -> str:
    """Returns a JSON string with the attributes of the specified target device.
    Always try this first when the user asks about a specific device.
    
    This tool is safe to call in parallel for multiple devices. When querying multiple devices,
    you should call this tool concurrently for all devices to improve performance.
    
    Inputs:
        target_device: (str) Target device to get the attributes from.

    Returns:
        str: JSON string with the following information:
        {
            "name": (str) Name of the device as onboarded in the inventory of this Cisco RADKit service
            "host": (str) IP address of the device
            "device_type": (str) Platform or Device Type type of the device
            "description": (str) Description of the device
            "terminal_config": (bool) The device's terminal is enabled for configurations
            "netconf_config": (bool) The device is enabled with NETCONF
            "snmp_version": (bool) The device is enabled with SNMP
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
            "snmp_version": false,
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
        Exception: Catches any potential errors during the fetching of the device's information in the Cisco RADKit service's inventory.
    """
    inventory_dict = {}
    inventory_dict["name"] = target_device
    radkit_service_handler = await _get_radkit_service_handler()
    
    loop = asyncio.get_event_loop()
    device_attributes = await loop.run_in_executor(
        None,
        lambda: radkit_service_handler.inventory[target_device].attributes.internal
    )
    
    for key in device_attributes.keys():
        inventory_dict[key] = device_attributes[key]
    
    return json.dumps(inventory_dict)


@mcp.tool()
async def exec_cli_commands_in_device(target_device:str, cli_commands:list[str], toolCallId: str = None) -> str:
    """Executes a CLI command or commands in the target device, and returns the raw result as text.
    Choose the CLI command or commands intelligently based on the device type (e.g., for Cisco IOS, use "show version" or "show interfaces" accordingly).
    If it is more than a single command, make sure that these commands can be executed sequentially safely.
    You can get the device type / platform using the tool get_device_inventory_names().
    - Use this only if:
        * The requested information is not available in get_device_attributes(), OR
        * The user explicitly asks to "run" or "execute" a command.

    Args:
        target_device (str): Target device to execute a CLI command at.
        cli_commands ([str]): CLI command or commands to execute in the target device. It can be any read/write command or commands.

    Returns:
        str: Raw output of the CLI command's execution
        
        Example:
        p0-2E#show ip interface brief
        Interface              IP-Address      OK? Method Status                Protocol
        Vlan1                  unassigned      YES NVRAM  up                    up      
        Vlan1021               192.168.123.1   YES NVRAM  up                    up      
        Vlan1022               172.16.123.1    YES NVRAM  up                    up      
        Vlan1023               172.16.121.1    YES NVRAM  up                    up      
        Vlan1025               172.16.126.1    YES NVRAM  up                    up      
        GigabitEthernet0/0     10.48.172.59    YES NVRAM  up                    up      
        GigabitEthernet1/0/1   unassigned      YES unset  down                  down    
        GigabitEthernet1/0/2   unassigned      YES unset  down                  down    
        GigabitEthernet1/0/3   192.168.122.35  YES NVRAM  up                    up      
        p0-2E#
        
    Raises:
        Exception: Catches any potential errors during the execution of the desired CLI command in the target device.
        If the exception reads "Access denied", it means that RBAC is enabled in the RADKit server, and the user with which this MCP server was onboarded is not allowed into this specific device, must likely because it is missing the appropiate RBAC tag, and that it needs to be granted permissions in the RADKit service.
    """
    radkit_service_handler = await _get_radkit_service_handler()
    
    loop = asyncio.get_event_loop()
    exec_result = await loop.run_in_executor(
        None,
        lambda: radkit_service_handler.inventory[target_device].exec(cli_commands).wait().result
    )

    # For multiple commands, result is a dict-like object with command as key
    result = exec_result.result

    # Concatenate all command outputs
    if hasattr(result, 'data'):
        output = result.data
    else:
        # result is dict-like: {command: response_object}
        output = "\n".join([resp.data for resp in result.values()])

    return output


if __name__ == "__main__":
    logger.info(f'✅ RADKit MCP Server running! (User {os.getenv("RADKIT_SERVICE_USERNAME")} for service {os.getenv("RADKIT_SERVICE_CODE")})')
    
    if transport == "https":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        
        logger.info(f"Starting MCP server with HTTPS transport on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
"""
Command execution tool for RADKit.

This module provides MCP tools for executing commands on
network devices via RADKit.
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


async def radkit_exec_command(
    device_name: str,
    commands: Union[str, list[str]],
    service_serial: Optional[str] = None,
    timeout: Optional[int] = 0,
    max_lines: Optional[int] = 800,
    reset_before: Optional[bool] = False,
    reset_after: Optional[bool] = False,
    sudo: Optional[bool] = False
) -> Union[dict, list[dict]]:
    """
    Execute command(s) on a RADKit-managed network device.

    This tool executes one or more commands on a network device managed by RADKit
    and returns the command output and execution status.

    Args:
        device_name: Name of the device in RADKit inventory (e.g., "router1")
        commands: Single command string or list of command strings to execute
                 (e.g., "show version" or ["show version", "show ip int brief"])
        service_serial: Optional service serial to override default. If not provided,
                       uses RADKIT_DEFAULT_SERVICE_SERIAL from environment.
        timeout: Execution timeout in seconds. Use 0 for no timeout (default: 0)
        max_lines: Maximum number of lines to return. Output exceeding this limit
                  will be truncated with a note (default: 800, use 0 for unlimited)
        reset_before: Reset device terminal before executing commands (default: False)
        reset_after: Reset device terminal after executing commands (default: False)
        sudo: Execute commands with sudo privileges (default: False)

    Returns:
        For single command: Dictionary with command result:
        {
            "device_name": "device-name",
            "command": "show version",
            "output": "Cisco IOS Software...",
            "status": "SUCCESS"
        }

        For multiple commands: List of dictionaries, one per command

    Raises:
        ValueError: If device not found in inventory
        Exception: If command execution fails

    Examples:
        # Execute single command
        result = radkit_exec_command("router1", "show version")

        # Execute multiple commands
        results = radkit_exec_command(
            "router1",
            ["show version", "show ip interface brief"]
        )

        # Execute with timeout
        result = radkit_exec_command(
            "router1",
            "show tech-support",
            timeout=300
        )

        # Use different service
        result = radkit_exec_command(
            "router1",
            "show version",
            service_serial="other-service"
        )
    """
    try:
        # Handle None values for optional parameters
        timeout = timeout if timeout is not None else 0
        max_lines = max_lines if max_lines is not None else 800
        reset_before = reset_before if reset_before is not None else False
        reset_after = reset_after if reset_after is not None else False
        sudo = sudo if sudo is not None else False

        # Get the appropriate service (synchronous operation)
        service = get_service(service_serial)

        # Normalize commands to consistent format (list)
        commands_list = [commands] if isinstance(commands, str) else commands
        if not commands_list:
            raise ValueError("At least one command must be provided")

        # Run command execution in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()

        def execute_commands():
            # Get device inventory by name
            inventory = service.inventory.filter("name", device_name)
            if not inventory:
                raise ValueError(f"Device '{device_name}' not found in RADKit inventory")

            # Execute command(s) with optional parameters
            if timeout == 0:
                response = inventory.exec(
                    commands_list,
                    reset_before=reset_before,
                    reset_after=reset_after,
                    sudo=sudo
                ).wait()
            else:
                response = inventory.exec(
                    commands_list,
                    timeout=timeout,
                    reset_before=reset_before,
                    reset_after=reset_after,
                    sudo=sudo
                ).wait(timeout)

            # Extract result for this device
            device_result = response.result[device_name]

            # Check if execution was successful
            if device_result.status.value != "SUCCESS":
                # Get status message if available
                status_msg = getattr(device_result, "status_message", "Unknown error")
                raise Exception(
                    f"Command execution failed on {device_name}: {status_msg}"
                )

            # Format output for each command
            results = []
            for cmd in device_result:
                cmd_result = device_result[cmd]

                # Get output and handle line truncation
                output = cmd_result.data
                truncated = False
                total_lines = 0

                if max_lines > 0:
                    lines = output.splitlines(keepends=True)
                    total_lines = len(lines)

                    if total_lines > max_lines:
                        # Keep first max_lines
                        truncated_output = ''.join(lines[:max_lines])
                        truncated_lines = total_lines - max_lines

                        # Add truncation notice
                        truncation_note = f"\n\n[OUTPUT TRUNCATED: {truncated_lines} lines omitted, showing first {max_lines} of {total_lines} lines]\n"
                        output = truncated_output + truncation_note
                        truncated = True

                result_entry = {
                    "device_name": device_name,
                    "command": cmd,
                    "output": output,
                    "status": cmd_result.status.value,
                    "truncated": truncated
                }

                if truncated:
                    result_entry["total_lines"] = total_lines
                    result_entry["displayed_lines"] = max_lines

                results.append(result_entry)

            # Return single result for single command, list for multiple
            return results[0] if len(results) == 1 else results

        return await loop.run_in_executor(None, execute_commands)

    except ValueError as ve:
        # Re-raise ValueError for device not found
        raise ve
    except Exception as e:
        raise Exception(
            f"Command execution failed on device {device_name}: {e}"
        ) from e

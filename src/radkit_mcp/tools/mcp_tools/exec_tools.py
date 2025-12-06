"""
MCP Exec Tool Registration

This module contains functions for registering command execution tools with FastMCP.
"""

from typing import Union, Optional

# Handle imports for both module and standalone execution
try:
    from ..exec import radkit_exec_command
except ImportError:
    from tools.exec import radkit_exec_command


def register_exec_tools(mcp):
    """
    Register command execution tools with the FastMCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def exec_cli_commands_in_device(
        target_device: str,
        cli_commands: Union[str, list[str]],
        timeout: Optional[int] = 0,
        max_lines: Optional[int] = 0,
        service_serial: Optional[str] = None,
        reset_before: Optional[bool] = False,
        reset_after: Optional[bool] = False,
        sudo: Optional[bool] = False
    ) -> str:
        """
        Executes a CLI command or commands in the target device, and returns the raw result as text.

        Choose the CLI command or commands intelligently based on the device type
        (e.g., for Cisco IOS, use "show version" or "show interfaces" accordingly).

        Optional parameters:
        - timeout: Command execution timeout (seconds, 0 = no timeout)
        - max_lines: Maximum lines of output (0 = unlimited)
        - service_serial: Override default service
        - reset_before: Reset device terminal before executing commands
        - reset_after: Reset device terminal after executing commands
        - sudo: Execute commands with sudo privileges

        Use this only if:
        * The requested information is not available in get_device_attributes(), OR
        * The user explicitly asks to "run" or "execute" a command.

        Args:
            target_device (str): Target device to execute a CLI command at.
            cli_commands (str | list[str]): CLI command or commands to execute.
            timeout (int, optional): Command execution timeout in seconds (0 = no timeout)
            max_lines (int, optional): Maximum lines to return (0 = unlimited)
            service_serial (str, optional): Override default service
            reset_before (bool, optional): Reset device terminal before execution
            reset_after (bool, optional): Reset device terminal after execution
            sudo (bool, optional): Execute with sudo privileges

        Returns:
            str: Raw output of the CLI command's execution

        Raises:
            Exception: If command execution fails. If exception reads "Access denied",
                      it means RBAC is enabled and user lacks permissions.
        """
        # Normalize command to list
        commands = [cli_commands] if isinstance(cli_commands, str) else cli_commands

        # Handle None values for optional parameters
        timeout = timeout if timeout is not None else 0
        max_lines = max_lines if max_lines is not None else 0
        reset_before = reset_before if reset_before is not None else False
        reset_after = reset_after if reset_after is not None else False
        sudo = sudo if sudo is not None else False

        # Call async tool function directly
        result = await radkit_exec_command(
            device_name=target_device,
            commands=commands,
            service_serial=service_serial,
            timeout=timeout,
            max_lines=max_lines,
            reset_before=reset_before,
            reset_after=reset_after,
            sudo=sudo
        )

        # Format output as string for backward compatibility
        if isinstance(result, dict):
            # Single command result
            output = result["output"]
            if result.get("truncated"):
                output += f"\n[Truncated: {result['displayed_lines']} of {result['total_lines']} lines shown]"
            return output
        else:
            # Multiple commands - concatenate outputs
            outputs = []
            for cmd_result in result:
                outputs.append(f"# Command: {cmd_result['command']}\n{cmd_result['output']}")
            return "\n\n".join(outputs)

    @mcp.tool()
    async def exec_command(
        device_name: str,
        commands: Union[str, list[str]],
        service_serial: Optional[str] = None,
        timeout: Optional[int] = 0,
        max_lines: Optional[int] = 2000,
        reset_before: Optional[bool] = False,
        reset_after: Optional[bool] = False,
        sudo: Optional[bool] = False
    ) -> Union[dict, list[dict]]:
        """
        Execute command(s) on a RADKit-managed network device (alternative interface to exec_cli_commands_in_device).

        Choose the CLI command or commands intelligently based on the device type
        (e.g., for Cisco IOS, use "show version" or "show interfaces" accordingly).

        Args:
            device_name: Name of the device in RADKit inventory
            commands: Single command string or list of command strings
            service_serial: Optional service serial to override default
            timeout: Execution timeout in seconds (0 = no timeout)
            max_lines: Maximum lines of output (default: 2000, use 0 for unlimited)
            reset_before: Reset device terminal before executing commands
            reset_after: Reset device terminal after executing commands
            sudo: Execute commands with sudo privileges

        Returns:
            Dictionary (single command) or list of dictionaries (multiple commands)
            with device_name, command, output, status, and truncation info
        """
        # Handle None values for optional parameters
        timeout = timeout if timeout is not None else 0
        max_lines = max_lines if max_lines is not None else 2000
        reset_before = reset_before if reset_before is not None else False
        reset_after = reset_after if reset_after is not None else False
        sudo = sudo if sudo is not None else False

        return await radkit_exec_command(
            device_name,
            commands,
            service_serial,
            timeout,
            max_lines,
            reset_before,
            reset_after,
            sudo
        )

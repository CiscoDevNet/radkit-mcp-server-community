"""MCP SCP file-transfer tool registration."""

import asyncio
import base64
import binascii
from typing import Optional

try:
    from ...client import get_service
except ImportError:
    from client import get_service


MAX_SCP_FILE_BYTES = 10 * 1024 * 1024


def _validate_remote_path(remote_path: str) -> None:
    if not remote_path or len(remote_path) > 4096 or "\0" in remote_path:
        raise ValueError("remote_path must be a non-empty device path up to 4096 characters")


def register_scp_tools(mcp):
    """Register bounded, in-memory SCP upload and download tools."""

    @mcp.tool()
    async def scp_download(
        device_name: str,
        remote_path: str,
        service_serial: Optional[str] = None,
    ) -> dict:
        """Download a file from a RADKit-managed device as base64.

        Files larger than 10 MiB are rejected. The MCP server filesystem is not
        used.
        """
        _validate_remote_path(remote_path)

        def download():
            service = get_service(service_serial)
            try:
                device = service.inventory[device_name]
            except KeyError as error:
                raise ValueError(f"Device '{device_name}' not found in RADKit inventory") from error

            connection = device.scp_download_to_stream(remote_path).wait()
            try:
                chunks = []
                remaining = MAX_SCP_FILE_BYTES + 1
                while remaining:
                    chunk = connection.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
            finally:
                connection.close()
                connection.wait_closed()

            data = b"".join(chunks)
            if len(data) > MAX_SCP_FILE_BYTES:
                raise ValueError("SCP download exceeds the 10 MiB limit")
            return data

        data = await asyncio.to_thread(download)
        return {
            "device_name": device_name,
            "remote_path": remote_path,
            "size": len(data),
            "content_base64": base64.b64encode(data).decode("ascii"),
        }

    @mcp.tool()
    async def scp_upload(
        device_name: str,
        remote_path: str,
        content_base64: str,
        confirm_write: bool = False,
        service_serial: Optional[str] = None,
    ) -> dict:
        """Upload a base64-encoded file to a RADKit-managed device via SCP.

        Files larger than 10 MiB are rejected. Existing remote files may be
        overwritten only when confirm_write is true. Call once without
        confirmation to preview the target and decoded size.
        """
        _validate_remote_path(remote_path)
        if len(content_base64) > 4 * ((MAX_SCP_FILE_BYTES + 2) // 3):
            raise ValueError("SCP upload exceeds the 10 MiB limit")
        try:
            data = base64.b64decode(content_base64, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("content_base64 must be valid base64") from error
        if len(data) > MAX_SCP_FILE_BYTES:
            raise ValueError("SCP upload exceeds the 10 MiB limit")
        if not confirm_write:
            return {
                "device_name": device_name,
                "remote_path": remote_path,
                "size": len(data),
                "status": "confirmation_required",
                "message": "Set confirm_write=true to write or overwrite this remote file.",
            }

        def upload():
            service = get_service(service_serial)
            try:
                device = service.inventory[device_name]
            except KeyError as error:
                raise ValueError(f"Device '{device_name}' not found in RADKit inventory") from error

            connection = device.scp_upload_from_stream(remote_path, len(data)).wait()
            try:
                connection.write(data)
            finally:
                connection.close()
                connection.wait_closed()

        await asyncio.to_thread(upload)
        return {
            "device_name": device_name,
            "remote_path": remote_path,
            "size": len(data),
            "status": "uploaded",
        }

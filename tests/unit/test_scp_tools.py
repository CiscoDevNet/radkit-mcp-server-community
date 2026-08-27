"""Unit coverage for bounded in-memory SCP tools."""

import base64
from types import SimpleNamespace

import pytest

from radkit_mcp.tools.mcp_tools import scp_tools


class MCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def register(function):
            self.tools[function.__name__] = function
            return function

        return register


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scp_download_and_upload_use_sdk_streams(monkeypatch):
    calls = []

    async def run_inline(function):
        return function()

    class Connection:
        def __init__(self, chunks=()):
            self.chunks = iter(chunks)

        def wait(self):
            calls.append("wait")
            return self

        def read(self, size):
            calls.append(("read", size))
            return next(self.chunks, b"")

        def write(self, data):
            calls.append(("write", data))

        def close(self):
            calls.append("close")

        def wait_closed(self):
            calls.append("wait_closed")

    class Device:
        def scp_download_to_stream(self, remote_path):
            calls.append(("download", remote_path))
            return Connection((b"file ", b"contents"))

        def scp_upload_from_stream(self, remote_path, size):
            calls.append(("upload", remote_path, size))
            return Connection()

    service = SimpleNamespace(inventory={"router1": Device()})
    monkeypatch.setattr(scp_tools, "get_service", lambda serial: service)
    monkeypatch.setattr(scp_tools.asyncio, "to_thread", run_inline)
    mcp = MCP()
    scp_tools.register_scp_tools(mcp)

    downloaded = await mcp.tools["scp_download"]("router1", "/tmp/source")
    preview = await mcp.tools["scp_upload"](
        "router1",
        "/tmp/destination",
        base64.b64encode(b"new contents").decode("ascii"),
    )
    uploaded = await mcp.tools["scp_upload"](
        "router1",
        "/tmp/destination",
        base64.b64encode(b"new contents").decode("ascii"),
        True,
    )

    assert downloaded == {
        "device_name": "router1",
        "remote_path": "/tmp/source",
        "size": 13,
        "content_base64": "ZmlsZSBjb250ZW50cw==",
    }
    assert preview == {
        "device_name": "router1",
        "remote_path": "/tmp/destination",
        "size": 12,
        "status": "confirmation_required",
        "message": "Set confirm_write=true to write or overwrite this remote file.",
    }
    assert uploaded == {
        "device_name": "router1",
        "remote_path": "/tmp/destination",
        "size": 12,
        "status": "uploaded",
    }
    assert calls == [
        ("download", "/tmp/source"),
        "wait",
        ("read", 64 * 1024),
        ("read", 64 * 1024),
        ("read", 64 * 1024),
        "close",
        "wait_closed",
        ("upload", "/tmp/destination", 12),
        "wait",
        ("write", b"new contents"),
        "close",
        "wait_closed",
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scp_rejects_invalid_or_oversized_input(monkeypatch):
    async def run_inline(function):
        return function()

    class Connection:
        def wait(self):
            return self

        def read(self, size):
            return b"big"

        def close(self):
            pass

        def wait_closed(self):
            pass

    device = SimpleNamespace(
        scp_download_to_stream=lambda remote_path: Connection(),
    )
    service = SimpleNamespace(inventory={"router1": device})
    monkeypatch.setattr(scp_tools, "get_service", lambda serial: service)
    monkeypatch.setattr(scp_tools.asyncio, "to_thread", run_inline)
    mcp = MCP()
    scp_tools.register_scp_tools(mcp)
    download = mcp.tools["scp_download"]
    upload = mcp.tools["scp_upload"]

    with pytest.raises(ValueError, match="valid base64"):
        await upload("router1", "/tmp/file", "not base64")
    monkeypatch.setattr(scp_tools, "MAX_SCP_FILE_BYTES", 2)
    with pytest.raises(ValueError, match="10 MiB limit"):
        await upload("router1", "/tmp/file", base64.b64encode(b"big").decode("ascii"))
    with pytest.raises(ValueError, match="10 MiB limit"):
        await download("router1", "/tmp/file")

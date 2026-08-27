"""Unit coverage for TCP port-forwarding tool registration."""

from types import SimpleNamespace

import pytest

from radkit_mcp.tools.mcp_tools import port_forwarding_tools


@pytest.mark.unit
@pytest.mark.asyncio
async def test_forward_tcp_port_starts_loopback_forwarder(monkeypatch):
    calls = []

    class Device:
        def forward_tcp_port(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                local_port=4443,
                destination_port=443,
                status=SimpleNamespace(value="RUNNING"),
            )

    service = SimpleNamespace(inventory={"router1": Device()})
    monkeypatch.setattr(
        port_forwarding_tools,
        "get_service",
        lambda serial: calls.append({"service_serial": serial}) or service,
    )

    class MCP:
        def __init__(self):
            self.tools = {}

        def tool(self):
            def register(function):
                self.tools[function.__name__] = function
                return function

            return register

    mcp = MCP()
    port_forwarding_tools.register_port_forwarding_tools(mcp)
    tool = mcp.tools["forward_tcp_port"]

    result = await tool("router1", 4443, 443, "service-serial")

    assert calls == [
        {"service_serial": "service-serial"},
        {"local_port": 4443, "destination_port": 443, "local_address": "localhost"},
    ]
    assert result == {
        "device_name": "router1",
        "local_address": "localhost",
        "local_port": 4443,
        "destination_port": 443,
        "status": "RUNNING",
    }

    with pytest.raises(ValueError, match="local_port must be an integer between 1 and 65535"):
        await tool("router1", 0, 443)

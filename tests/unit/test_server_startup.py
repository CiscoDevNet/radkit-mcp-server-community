"""Unit tests for MCP server transport startup validation."""

from types import SimpleNamespace

import pytest

from radkit_mcp import server


def _settings(transport="sse", host="127.0.0.1", allowed=False):
    return SimpleNamespace(
        mcp_transport=transport,
        mcp_host=host,
        mcp_port=8000,
        allow_insecure_network_bind=allowed,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "127.0.0.2",
        "::1",
        "0:0:0:0:0:0:0:1",
        "::ffff:127.0.0.1",
        "::ffff:7f00:1",
        "localhost",
        "LOCALHOST.",
    ],
)
@pytest.mark.parametrize("transport", ["sse", "http"])
def test_loopback_network_bind_starts(monkeypatch, host, transport):
    """All supported loopback forms start without the insecure override."""
    run_calls = []
    monkeypatch.setattr(
        server,
        "get_settings",
        lambda: _settings(transport=transport, host=host),
    )
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: run_calls.append(kwargs))

    server.main()

    assert run_calls == [{"transport": transport, "host": host, "port": 8000}]


@pytest.mark.unit
def test_non_loopback_bind_is_refused_without_override(monkeypatch):
    """An unauthenticated network bind fails closed by default."""
    run_calls = []
    monkeypatch.setattr(server, "get_settings", lambda: _settings(host="0.0.0.0"))
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: run_calls.append(kwargs))

    with pytest.raises(SystemExit, match="1") as exc_info:
        server.main()

    assert exc_info.value.code == 1
    assert run_calls == []


@pytest.mark.unit
def test_non_loopback_bind_starts_with_explicit_override(monkeypatch):
    """An explicit operator override allows a non-loopback bind."""
    run_calls = []
    monkeypatch.setattr(
        server,
        "get_settings",
        lambda: _settings(host="0.0.0.0", allowed=True),
    )
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: run_calls.append(kwargs))

    server.main()

    assert run_calls == [
        {"transport": "sse", "host": "0.0.0.0", "port": 8000}
    ]


@pytest.mark.unit
def test_stdio_ignores_network_bind_validation(monkeypatch):
    """STDIO remains local and does not require the network override."""
    run_calls = []
    monkeypatch.setattr(
        server,
        "get_settings",
        lambda: _settings(transport="stdio", host="0.0.0.0"),
    )
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: run_calls.append(kwargs))

    server.main()

    assert run_calls == [{"transport": "stdio"}]

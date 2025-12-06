"""
Pytest configuration for RADKit FastMCP server tests.

This file configures pytest for async tests and provides shared fixtures.
"""

import pytest
import os
from dotenv import load_dotenv


# Load environment variables before tests run
load_dotenv()


@pytest.fixture(scope="session")
def test_device_name():
    """
    Get test device name from environment variable.

    Set RADKIT_TEST_DEVICE in your .env file to specify which device
    to use for integration tests.

    Example:
        RADKIT_TEST_DEVICE=router1
    """
    device = os.getenv("RADKIT_TEST_DEVICE")
    if not device:
        pytest.skip("RADKIT_TEST_DEVICE not set - skipping integration test requiring device")
    return device


@pytest.fixture(scope="session")
def test_snmp_oid():
    """
    Get test SNMP OID from environment variable.

    Defaults to sysDescr OID if not specified.
    """
    return os.getenv("RADKIT_TEST_SNMP_OID", "1.3.6.1.2.1.1.1.0")


@pytest.fixture(scope="session")
def test_command():
    """
    Get test CLI command from environment variable.

    Defaults to 'show clock' if not specified.
    """
    return os.getenv("RADKIT_TEST_COMMAND", "show clock")


@pytest.fixture(scope="session", autouse=True)
def verify_environment(request):
    """
    Verify required environment variables are present for integration tests.

    Only checks for integration tests (marked with @pytest.mark.integration).
    """
    # Check if this is an integration test
    if "integration" in request.keywords:
        required_vars = [
            "RADKIT_IDENTITY",
            "RADKIT_DEFAULT_SERVICE_SERIAL",
            "RADKIT_CERT_B64",
            "RADKIT_KEY_B64",
            "RADKIT_CA_B64",
            "RADKIT_KEY_PASSWORD_B64"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.skip(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please create a .env file with all required credentials."
            )

    # Print environment info for test runs
    if os.getenv("RADKIT_IDENTITY"):
        print(f"\nRunning tests with:")
        print(f"  Identity: {os.getenv('RADKIT_IDENTITY')}")
        print(f"  Service: {os.getenv('RADKIT_DEFAULT_SERVICE_SERIAL')}")
        print(f"  Test Device: {os.getenv('RADKIT_TEST_DEVICE', 'Not set')}\n")


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Configure event loop policy for async tests.

    This ensures pytest-asyncio uses the correct event loop.
    """
    import asyncio
    return asyncio.get_event_loop_policy()


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require real devices and RADKit service)"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (no real devices needed)"
    )
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as an async test"
    )


def pytest_report_header(config):
    """Add custom header to pytest output."""
    return [
        "RADKit FastMCP Server Tests",
        "Unit tests: No real devices required",
        "Integration tests: Require real devices and RADKit service"
    ]

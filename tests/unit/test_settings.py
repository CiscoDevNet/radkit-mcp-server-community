"""
Unit tests for settings management module.

These tests verify pydantic-settings configuration and environment variable handling.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.unit
def test_settings_singleton():
    """Test that get_settings returns the same instance."""
    from radkit_mcp.settings import get_settings

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2, "get_settings should return singleton instance"


@pytest.mark.unit
def test_settings_structure():
    """Test that settings has expected attributes."""
    from radkit_mcp.settings import RADKitSettings

    # Create a new instance for testing
    settings = RADKitSettings()

    # Check that key attributes exist
    assert hasattr(settings, 'identity')
    assert hasattr(settings, 'default_service_serial')
    assert hasattr(settings, 'cert_b64')
    assert hasattr(settings, 'key_b64')
    assert hasattr(settings, 'ca_b64')
    assert hasattr(settings, 'mcp_transport')
    assert hasattr(settings, 'mcp_host')
    assert hasattr(settings, 'mcp_port')


@pytest.mark.unit
def test_settings_property_methods():
    """Test that settings has property methods for aliases."""
    from radkit_mcp.settings import RADKitSettings

    settings = RADKitSettings()

    # Check that property methods exist
    assert hasattr(settings, 'radkit_identity')
    assert hasattr(settings, 'radkit_service_serial')
    assert hasattr(settings, 'radkit_key_password')
    assert hasattr(settings, 'has_base64_credentials')


@pytest.mark.unit
def test_settings_has_base64_credentials_method():
    """Test has_base64_credentials returns boolean."""
    from radkit_mcp.settings import get_settings

    settings = get_settings()
    result = settings.has_base64_credentials()

    # Should return a boolean
    assert isinstance(result, bool)

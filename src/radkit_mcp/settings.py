"""
Settings management for RADKit MCP Server using pydantic-settings.

This module provides centralized configuration management

Environment Variables (with aliases):
- RADKIT_IDENTITY (alias: RADKIT_SERVICE_USERNAME)
- RADKIT_DEFAULT_SERVICE_SERIAL (alias: RADKIT_SERVICE_CODE)
- RADKIT_KEY_PASSWORD_B64 (alias: RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64)
- RADKIT_CERT_B64
- RADKIT_KEY_B64
- RADKIT_CA_B64
- MCP_TRANSPORT
- MCP_HOST
- MCP_PORT
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RADKitSettings(BaseSettings):
    """RADKit MCP Server settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Authentication - Identity
    identity: Optional[str] = Field(
        default=None,
        validation_alias="RADKIT_IDENTITY",
        description="RADKit user identity (email or username)"
    )

    # Alias for identity
    service_username: Optional[str] = Field(
        default=None,
        alias="RADKIT_SERVICE_USERNAME",
        description="Alias for RADKIT_IDENTITY"
    )

    # Service Configuration
    default_service_serial: Optional[str] = Field(
        default=None,
        validation_alias="RADKIT_DEFAULT_SERVICE_SERIAL",
        description="Default RADKit service serial number"
    )

    # Alias for service serial
    service_code: Optional[str] = Field(
        default=None,
        alias="RADKIT_SERVICE_CODE",
        description="Alias for RADKIT_DEFAULT_SERVICE_SERIAL"
    )

    # Certificate Authentication (Base64 encoded)
    cert_b64: Optional[str] = Field(
        default=None,
        alias="RADKIT_CERT_B64",
        description="Base64-encoded certificate.pem"
    )

    key_b64: Optional[str] = Field(
        default=None,
        alias="RADKIT_KEY_B64",
        description="Base64-encoded private_key_encrypted.pem"
    )

    ca_b64: Optional[str] = Field(
        default=None,
        alias="RADKIT_CA_B64",
        description="Base64-encoded chain.pem"
    )

    key_password_b64: Optional[str] = Field(
        default=None,
        validation_alias="RADKIT_KEY_PASSWORD_B64",
        description="Base64-encoded private key password"
    )

    # Alias for password
    client_private_key_password_base64: Optional[str] = Field(
        default=None,
        alias="RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64",
        description="Alias for RADKIT_KEY_PASSWORD_B64"
    )

    # MCP Server Configuration
    mcp_transport: str = Field(
        default="stdio",
        alias="MCP_TRANSPORT",
        description="MCP transport mode (stdio, https, sse)"
    )

    mcp_host: str = Field(
        default="0.0.0.0",
        alias="MCP_HOST",
        description="MCP server host"
    )

    mcp_port: int = Field(
        default=8000,
        alias="MCP_PORT",
        description="MCP server port"
    )

    @property
    def radkit_identity(self) -> Optional[str]:
        """Get identity with fallback to alias."""
        return self.identity or self.service_username

    @property
    def radkit_service_serial(self) -> Optional[str]:
        """Get service serial with fallback to alias."""
        return self.default_service_serial or self.service_code

    @property
    def radkit_key_password(self) -> Optional[str]:
        """Get key password with fallback to alias."""
        return self.key_password_b64 or self.client_private_key_password_base64

    def has_base64_credentials(self) -> bool:
        """Check if all base64-encoded certificate credentials are available."""
        return all([
            self.cert_b64,
            self.key_b64,
            self.ca_b64,
            self.radkit_key_password
        ])


# Global settings instance
_settings: Optional[RADKitSettings] = None


def get_settings() -> RADKitSettings:
    """
    Get the global settings instance (singleton pattern).

    Returns:
        RADKitSettings instance
    """
    global _settings
    if _settings is None:
        _settings = RADKitSettings()
    return _settings


def reload_settings() -> RADKitSettings:
    """
    Reload settings from environment (useful for testing).

    Returns:
        Newly loaded RADKitSettings instance
    """
    global _settings
    _settings = RADKitSettings()
    return _settings

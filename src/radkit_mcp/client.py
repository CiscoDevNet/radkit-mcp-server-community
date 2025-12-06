"""
RADKit client lifecycle management for FastMCP.

This module manages the RADKit client connection, authentication,
and service caching for the FastMCP server.

Supports dual-mode authentication:
1. Environment variables (RADKIT_CERT_B64, etc.) - for containers
2. Local certificate files (~/.radkit/) - for local development
3. Certificate login with username/password - for interactive use
"""

import sys
from pathlib import Path
from typing import Any, Optional
from radkit_client.sync import Client

# Import auth and settings modules
try:
    from .auth import CertificateCredentials, load_certificates_from_env, load_certificates_from_files
    from .settings import get_settings
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from auth import CertificateCredentials, load_certificates_from_env, load_certificates_from_files
    from settings import get_settings


# Global state
_radkit_client: Optional[Client] = None
_radkit_services: dict[str, Any] = {}
_cert_credentials: Optional[CertificateCredentials] = None


def _has_base64_env_vars() -> bool:
    """
    Check if base64-encoded certificate environment variables are available.

    Returns:
        True if all required base64 env vars are set
    """
    settings = get_settings()
    return settings.has_base64_credentials()


def _has_local_cert_dir() -> bool:
    """
    Check if local RADKit certificate directory exists.

    Returns:
        True if ~/.radkit directory exists with certificates
    """
    settings = get_settings()
    username = settings.radkit_identity
    if not username:
        return False

    domain = "prod.radkit-cloud.cisco.com"
    cert_dir = Path.home() / ".radkit" / "identities" / domain / username

    if not cert_dir.exists():
        return False

    # Check for required files
    required_files = ["certificate.pem", "private_key_encrypted.pem", "chain.pem"]
    return all((cert_dir / f).exists() for f in required_files)


def _get_auth_mode() -> str:
    """
    Determine which authentication mode to use.

    Returns:
        "env_vars", "local_certs", or "username_login"
    """
    settings = get_settings()

    # Priority 1: Environment variables (container-friendly)
    if _has_base64_env_vars():
        return "env_vars"

    # Priority 2: Local certificate directory (local development)
    if _has_local_cert_dir():
        return "local_certs"

    # Priority 3: Certificate login with username (interactive)
    if settings.radkit_identity:
        return "username_login"

    raise ValueError(
        "No authentication method available. Please set either:\n"
        "1. Environment variables: RADKIT_CERT_B64, RADKIT_KEY_B64, etc.\n"
        "2. Local certificates: ~/.radkit/identities/\n"
        "3. Username: RADKIT_IDENTITY (or RADKIT_SERVICE_USERNAME)"
    )


def initialize_radkit_client(client: Client) -> None:
    """
    Initialize the RADKit client with appropriate authentication method.

    This function auto-detects the available authentication method:
    1. Base64 environment variables (for containers)
    2. Local certificate directory (for local development)
    3. Certificate login with username (for interactive use)

    Args:
        client: RADKit client instance from Client.create()

    Raises:
        ValueError: If no authentication method is available
        Exception: If authentication or connection fails
    """
    global _radkit_client, _cert_credentials, _radkit_services

    # Get settings
    settings = get_settings()

    # Determine authentication mode
    auth_mode = _get_auth_mode()
    print(f"Using authentication mode: {auth_mode}")

    # Get identity and service serial
    identity = settings.radkit_identity
    default_service_serial = settings.radkit_service_serial

    if not identity:
        raise ValueError("Environment variable RADKIT_IDENTITY (or RADKIT_SERVICE_USERNAME) is required")

    if not default_service_serial:
        raise ValueError("Environment variable RADKIT_DEFAULT_SERVICE_SERIAL (or RADKIT_SERVICE_CODE) is required")

    # Authenticate based on mode
    if auth_mode == "env_vars":
        # Mode 1: Base64 environment variables (container deployment)
        print("Loading certificate credentials from environment variables...")
        _cert_credentials = load_certificates_from_env()

        print(f"Authenticating as {identity} (base64 env vars)...")
        client.certificate_login(
            identity=identity,
            ca_path=_cert_credentials.ca_path,
            cert_path=_cert_credentials.cert_path,
            key_path=_cert_credentials.key_path,
            private_key_password=_cert_credentials.password
        )

    elif auth_mode == "local_certs":
        # Mode 2: Local certificate directory (local development)
        print(f"Loading certificates from ~/.radkit/identities/...")

        domain = "prod.radkit-cloud.cisco.com"
        cert_dir = Path.home() / ".radkit" / "identities" / domain / identity

        # Get password from settings
        password_b64 = settings.radkit_key_password
        if not password_b64:
            raise ValueError("Environment variable RADKIT_KEY_PASSWORD_B64 (or RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64) is required for local cert auth")

        import base64
        password = base64.b64decode(password_b64).decode("utf-8")

        # Load from local files
        _cert_credentials = load_certificates_from_files(
            cert_path=str(cert_dir / "certificate.pem"),
            key_path=str(cert_dir / "private_key_encrypted.pem"),
            ca_path=str(cert_dir / "chain.pem"),
            password=password
        )

        print(f"Authenticating as {identity} (local certs)...")
        client.certificate_login(
            identity=identity,
            ca_path=_cert_credentials.ca_path,
            cert_path=_cert_credentials.cert_path,
            key_path=_cert_credentials.key_path,
            private_key_password=_cert_credentials.password
        )

    else:  # username_login
        # Mode 3: Certificate login with username (backward compatibility)
        print(f"Authenticating as {identity} (certificate login)...")
        client.certificate_login(identity)

    # Store client reference
    _radkit_client = client
    print("✓ Authentication successful")

    # Connect to default service
    print(f"Connecting to default service: {default_service_serial}...")
    try:
        service = client.service(default_service_serial).wait()
        _radkit_services[default_service_serial] = service
        print(f"✓ Connected to service: {default_service_serial}")
    except Exception as e:
        print(f"Warning: Failed to connect to default service {default_service_serial}: {e}")
        print("Service will be connected on first use")


def get_service(service_serial: Optional[str] = None) -> Any:
    """
    Get a RADKit service by serial number.

    Args:
        service_serial: Service serial number. If None, uses default from environment.

    Returns:
        RADKit service object

    Raises:
        ValueError: If no service serial provided and no default set
        RuntimeError: If RADKit client not initialized
        Exception: If service connection fails
    """
    global _radkit_client, _radkit_services

    if _radkit_client is None:
        raise RuntimeError("RADKit client not initialized. Call initialize_radkit_client() first.")

    # Get settings
    settings = get_settings()

    # Determine which service serial to use
    serial = service_serial or settings.radkit_service_serial
    if not serial:
        raise ValueError(
            "No service serial provided and RADKIT_DEFAULT_SERVICE_SERIAL (or RADKIT_SERVICE_CODE) not set"
        )

    # Return cached service if available
    if serial in _radkit_services:
        return _radkit_services[serial]

    # Connect to new service
    print(f"Connecting to service: {serial}...")
    try:
        service = _radkit_client.service(serial).wait()
        _radkit_services[serial] = service
        print(f"✓ Connected to service: {serial}")
        return service
    except Exception as e:
        raise Exception(f"Failed to connect to service {serial}: {e}") from e


def cleanup_cert_files() -> None:
    """
    Clean up temporary certificate files.

    This should be called when shutting down the FastMCP server.
    Only cleans up if certificates were loaded from environment variables.
    """
    global _cert_credentials

    if _cert_credentials:
        print("Cleaning up temporary certificate files...")
        _cert_credentials.cleanup()
        _cert_credentials = None


def get_client() -> Optional[Client]:
    """
    Get the global RADKit client instance.

    Returns:
        RADKit client or None if not initialized
    """
    return _radkit_client


def is_initialized() -> bool:
    """
    Check if RADKit client is initialized.

    Returns:
        True if client is initialized, False otherwise
    """
    return _radkit_client is not None

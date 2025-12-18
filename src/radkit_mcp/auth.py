"""
Certificate authentication handler for RADKit.

This module handles loading certificate credentials from base64-encoded
environment variables and preparing them for RADKit certificate login.
"""

import base64
import os
import sys
import tempfile
from pathlib import Path
from typing import Tuple, Optional

# Import settings
try:
    from .settings import get_settings
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from settings import get_settings


class CertificateCredentials:
    """Container for certificate credentials and temporary file paths."""

    def __init__(
        self,
        ca_path: str,
        cert_path: str,
        key_path: str,
        password: str,
        temp_files: list[str]
    ):
        self.ca_path = ca_path
        self.cert_path = cert_path
        self.key_path = key_path
        self.password = password
        self._temp_files = temp_files

    def cleanup(self) -> None:
        """Clean up temporary certificate files."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                # Log but don't fail on cleanup errors
                print(f"Warning: Failed to remove temp file {temp_file}: {e}")


def _decode_base64_env_var(env_var_name: str) -> bytes:
    """
    Decode a base64-encoded environment variable.

    Args:
        env_var_name: Name of the environment variable

    Returns:
        Decoded bytes

    Raises:
        ValueError: If environment variable is missing or invalid
    """
    value = os.getenv(env_var_name)
    if not value:
        raise ValueError(f"Environment variable {env_var_name} is not set")

    try:
        return base64.b64decode(value)
    except Exception as e:
        raise ValueError(
            f"Failed to decode base64 from {env_var_name}: {e}"
        ) from e


def _write_temp_file(content: bytes, suffix: str = ".pem") -> str:
    """
    Write content to a temporary file.

    Args:
        content: Binary content to write
        suffix: File suffix (default: .pem)

    Returns:
        Path to the temporary file

    Raises:
        IOError: If file cannot be written
    """
    try:
        # Create temp file that won't be auto-deleted
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=suffix,
            delete=False
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        raise IOError(f"Failed to write temporary file: {e}") from e


def load_certificates_from_env() -> CertificateCredentials:
    """
    Load certificate credentials from environment variables.

    Expected environment variables:
        - RADKIT_CERT_B64: Base64-encoded certificate.pem
        - RADKIT_KEY_B64: Base64-encoded private_key_encrypted.pem
        - RADKIT_CA_B64: Base64-encoded chain.pem
        - RADKIT_KEY_PASSWORD_B64 (or RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64): Base64-encoded private key password

    Returns:
        CertificateCredentials object with paths to temporary files

    Raises:
        ValueError: If required environment variables are missing or invalid
        IOError: If temporary files cannot be created
    """
    temp_files = []

    try:
        # Get settings for accessing environment variables with aliases
        settings = get_settings()

        # Decode certificate files from environment
        cert_content = _decode_base64_env_var("RADKIT_CERT_B64")
        key_content = _decode_base64_env_var("RADKIT_KEY_B64")
        ca_content = _decode_base64_env_var("RADKIT_CA_B64")

        # Decode password (as string) - use settings to get with alias support
        password_b64 = settings.radkit_key_password
        if not password_b64:
            raise ValueError("Environment variable RADKIT_KEY_PASSWORD_B64 (or RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64) is not set")

        try:
            password = base64.b64decode(password_b64).decode("utf-8")
        except Exception as e:
            raise ValueError(
                f"Failed to decode password from RADKIT_KEY_PASSWORD_B64: {e}"
            ) from e

        # Write certificate files to temporary locations
        cert_path = _write_temp_file(cert_content, suffix="_cert.pem")
        temp_files.append(cert_path)

        key_path = _write_temp_file(key_content, suffix="_key.pem")
        temp_files.append(key_path)

        ca_path = _write_temp_file(ca_content, suffix="_ca.pem")
        temp_files.append(ca_path)

        return CertificateCredentials(
            ca_path=ca_path,
            cert_path=cert_path,
            key_path=key_path,
            password=password,
            temp_files=temp_files
        )

    except Exception:
        # Clean up any temporary files created before the error
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        raise


def load_certificates_from_files(
    cert_path: str,
    key_path: str,
    ca_path: str,
    password: str
) -> CertificateCredentials:
    """
    Load certificate credentials from existing files (for local development).

    Args:
        cert_path: Path to certificate.pem
        key_path: Path to private_key_encrypted.pem
        ca_path: Path to chain.pem
        password: Private key password

    Returns:
        CertificateCredentials object (no temp files to clean up)

    Raises:
        FileNotFoundError: If certificate files don't exist
    """
    # Verify files exist
    for path in [cert_path, key_path, ca_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Certificate file not found: {path}")

    return CertificateCredentials(
        ca_path=ca_path,
        cert_path=cert_path,
        key_path=key_path,
        password=password,
        temp_files=[]  # No temp files to clean up
    )

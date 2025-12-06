#!/usr/bin/env python3
"""
Enroll RADKit Client for Certificate Authentication.

This script helps you enroll your RADKit client to enable certificate-based
authentication. You must be enrolled before you can use the FastMCP server.

After enrollment, run scripts/build_env.py to create your .env file.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from radkit_client.sync import Client
except ImportError:
    print("Error: radkit_client not installed")
    print("Please install RADKit:")
    print("  uv pip install /path/to/cisco_radkit_*.whl")
    sys.exit(1)


def print_banner():
    """Print script banner."""
    print("=" * 70)
    print("RADKit Client Enrollment")
    print("=" * 70)
    print("""
This script will enroll your RADKit client for certificate authentication.

You will:
1. Authenticate via SSO (browser will open)
2. Create a password to protect your private key
3. Receive a client certificate for future authentication

After enrollment, run scripts/build_env.py to create your .env file.
""")
    print("=" * 70)


def main():
    """Main enrollment function."""
    print_banner()

    # Get identity
    identity = input("\nEnter your Cisco email address: ").strip()
    if not identity:
        print("Error: Email address is required")
        sys.exit(1)

    # Confirm
    print(f"\nYou will enroll as: {identity}")
    confirm = input("Continue? [y/N]: ").strip().lower()

    if confirm != 'y':
        print("Enrollment cancelled")
        sys.exit(0)

    print("\n" + "=" * 70)
    print("Starting RADKit client...")
    print("=" * 70)

    try:
        with Client.create() as client:
            # Authenticate with SSO
            print(f"\nStep 1: Authenticating via SSO as {identity}")
            print("A browser window will open for authentication...")
            print()

            client.sso_login(identity)

            print("\n✓ SSO authentication successful!")

            # Enroll client
            print("\n" + "=" * 70)
            print("Step 2: Enrolling client")
            print("=" * 70)
            print("""
You will now be prompted to create a password for your private key.

IMPORTANT:
- Choose a secure password
- Remember this password - you'll need it for build_env.py
- This password protects your client certificate's private key
""")

            client.enroll_client()

            print("\n" + "=" * 70)
            print("✓ CLIENT ENROLLMENT SUCCESSFUL!")
            print("=" * 70)
            print(f"""
Your client has been enrolled successfully!

Certificate files saved to:
  ~/.radkit/identities/prod.radkit-cloud.cisco.com/{identity}/

Files created:
  - certificate.pem              (your client certificate)
  - private_key_encrypted.pem    (your private key, password-protected)
  - chain.pem                    (CA certificate chain)

Next steps:
1. Run the environment builder:
   python scripts/build_env.py

2. Test your setup:
   .venv/bin/python tests/test_integration.py

3. Start the FastMCP server:
   fastmcp dev src/radkit_fastmcp/server.py
""")
            print("=" * 70)

    except Exception as e:
        print(f"\n✗ Enrollment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nEnrollment cancelled by user")
        sys.exit(1)

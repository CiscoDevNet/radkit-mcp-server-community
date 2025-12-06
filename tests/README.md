# RADKit MCP Server Tests

This directory contains the test suite for the RADKit MCP Server, organized into unit tests and integration tests.

## Test Organization

```
tests/
├── unit/                    # Unit tests (no real devices needed)
│   ├── test_settings.py     # Settings and configuration tests
│   └── test_server_tools.py # Server tool registration tests
├── integration/             # Integration tests (require real devices)
│   ├── test_radkit_integration.py  # RADKit API integration tests
│   └── test_mcp_protocol.py        # MCP protocol tests
├── conftest.py              # Shared pytest fixtures and configuration
└── README.md                # This file
```

## Test Types

### Unit Tests (`tests/unit/`)

Unit tests do not require real network devices or RADKit service credentials. They test:
- Settings and configuration management
- Type annotations and signatures
- Tool registration
- Logic and validation

**Run unit tests only:**
```bash
pytest tests/unit/ -v -m unit
```

### Integration Tests (`tests/integration/`)

Integration tests require real network devices and RADKit service credentials. They test:
- Authentication with RADKit service
- SNMP operations on real devices
- Command execution on real devices
- MCP protocol interactions
- End-to-end functionality

**Run integration tests only:**
```bash
pytest tests/integration/ -v -m integration
```

## Configuration

### Environment Variables

Integration tests require the following environment variables in your `.env` file:

```bash
# Required for all integration tests
RADKIT_IDENTITY=user@example.com
RADKIT_DEFAULT_SERVICE_SERIAL=your-service-serial
RADKIT_CERT_B64=<base64-encoded-cert>
RADKIT_KEY_B64=<base64-encoded-key>
RADKIT_CA_B64=<base64-encoded-ca>
RADKIT_KEY_PASSWORD_B64=<base64-encoded-password>

# Required for device-specific integration tests
RADKIT_TEST_DEVICE=router1          # Your test device name

# Optional: Override defaults
RADKIT_TEST_SNMP_OID=1.3.6.1.2.1.1.1.0   # Default: sysDescr
RADKIT_TEST_COMMAND=show clock            # Default: show clock
```

**Important:** The `RADKIT_TEST_DEVICE` variable specifies which device from your RADKit inventory to use for testing. Set this to a device you have access to (e.g., `router1`, `router2`, etc.).

### Test Device Requirements

For integration tests, your test device should:
- Be onboarded in your RADKit service inventory
- Have SNMP enabled (for SNMP tests)
- Support CLI commands (for exec tests)
- Be accessible from your RADKit service

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Only Unit Tests
```bash
pytest tests/unit/ -v -m unit
```

### Run Only Integration Tests
```bash
pytest tests/integration/ -v -m integration
```

### Run Specific Test File
```bash
pytest tests/unit/test_settings.py -v
pytest tests/integration/test_radkit_integration.py -v
```

### Run Specific Test Function
```bash
pytest tests/unit/test_settings.py::test_settings_singleton -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src/radkit_mcp --cov-report=html
```

## Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.unit` - Unit tests (no real devices)
- `@pytest.mark.integration` - Integration tests (require real devices)
- `@pytest.mark.asyncio` - Async tests

### Skip Integration Tests
```bash
pytest tests/ -v -m "not integration"
```

### Run Only Integration Tests
```bash
pytest tests/ -v -m integration
```

## Adding New Tests

### Adding Unit Tests

1. Create a new file in `tests/unit/` starting with `test_`
2. Mark tests with `@pytest.mark.unit`
3. Mock external dependencies (RADKit client, devices)
4. Focus on testing logic, not external integrations

Example:
```python
import pytest

@pytest.mark.unit
def test_my_function():
    """Test my function logic."""
    from src.radkit_mcp.module import my_function
    result = my_function("input")
    assert result == "expected"
```

### Adding Integration Tests

1. Create a new file in `tests/integration/` starting with `test_`
2. Mark tests with `@pytest.mark.integration`
3. Use fixtures: `test_device_name`, `test_snmp_oid`, `test_command`
4. Test real interactions with devices and RADKit service

Example:
```python
import pytest

@pytest.mark.integration
async def test_real_snmp_operation(test_device_name, test_snmp_oid):
    """Test SNMP operation on real device."""
    from radkit_mcp import client as radkit_client_module
    from radkit_mcp.tools.snmp import radkit_snmp_get
    from radkit_client.sync import Client

    try:
        with Client.create() as client:
            radkit_client_module.initialize_radkit_client(client)
            result = await radkit_snmp_get(test_device_name, test_snmp_oid)
            assert len(result) > 0
    finally:
        radkit_client_module.cleanup_cert_files()
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Run only unit tests (safe for CI without credentials)
pytest tests/unit/ -v -m unit

# Run integration tests only if credentials are available
if [ -n "$RADKIT_TEST_DEVICE" ]; then
  pytest tests/integration/ -v -m integration
fi
```

## Troubleshooting

### "RADKIT_TEST_DEVICE not set"

Integration tests require `RADKIT_TEST_DEVICE` to be set. Add it to your `.env` file:
```bash
RADKIT_TEST_DEVICE=your-device-name
```

### "Missing required environment variables"

Ensure all RADKit credentials are set in your `.env` file. See the Configuration section above.

### "Device not found in inventory"

The device specified in `RADKIT_TEST_DEVICE` must exist in your RADKit service inventory. Verify with:
```bash
python -c "from radkit_client.sync import Client; print(list(Client.create().inventory.values()))"
```

## Best Practices

1. **Keep unit tests fast** - Mock external dependencies
2. **Use fixtures** - Share common setup code via conftest.py
3. **Test one thing** - Each test should verify one behavior
4. **Descriptive names** - Test names should describe what they test
5. **Clean up resources** - Use try/finally for cleanup in integration tests
6. **Mark appropriately** - Always mark tests as `@pytest.mark.unit` or `@pytest.mark.integration`

# Security Policies and Procedures

This document outlines security procedures and general policies for the `radkit-mcp-server-community` project.

**⚠️ IMPORTANT:** This is **example/proof-of-concept code** intended for learning and evaluation purposes **only**. See [Security Notice for Network Transports](#security-notice-for-network-transports) before deploying.

- [Security Notice for Network Transports](#security-notice-for-network-transports)
- [Disclosing a security issue](#disclosing-a-security-issue)
- [Vulnerability management](#vulnerability-management)
- [Suggesting changes](#suggesting-changes)

## Security Notice for Network Transports

### Default Configuration (Secure)
The default MCP transport is **`stdio`** (standard input/output), which is **local-only and not network-exposed**. This is the recommended configuration for production use with local MCP clients like Claude Desktop.

### Network Transports (SSE/HTTP) — Important Security Considerations

If you choose to use `sse` or `http` transport for network access:

#### ⚠️ Known Limitations
1. **No MCP Client Authentication:** The current implementation does not authenticate MCP clients. Any client that can reach the server can invoke all exposed MCP tools.
2. **Network Exposure Risk:** By default, the server binds to `127.0.0.1` (localhost). If changed to `0.0.0.0` or other network addresses, the server becomes accessible from the network without authentication.
3. **Tool Exposure:** Exposed MCP tools provide privileged access:
   - `exec_cli_commands_in_device`: arbitrary CLI execution on enrolled Cisco devices
   - `exec_command`: additional command execution vector
   - `snmp_get`: SNMP read access to managed infrastructure
   - Device inventory and attribute enumeration

#### ✅ Recommendations for Network Deployments
- **Keep default binding:** Use `MCP_HOST=127.0.0.1` (the default)
- **Implement network isolation:** Use firewall rules, VPCs, or network policies to restrict access
- **Add authentication layer:** Consider implementing FastMCP middleware with bearer tokens or other authentication mechanisms
- **Use TLS/SSL:** Encrypt network communications between client and server
- **Review access controls:** Understand the security implications of the exposed tools and network configuration

#### Examples of Secure Network Deployment
```bash
# Recommended: Use localhost with firewall/network policy to restrict access
MCP_TRANSPORT=sse
MCP_HOST=127.0.0.1  # Default. Do not change unless you understand the risks
MCP_PORT=8000

# If network access is absolutely required:
# 1. Implement FastMCP authentication middleware
# 2. Use TLS/SSL encryption
# 3. Restrict network access via firewall rules
# 4. Monitor and log all access to sensitive tools
```

#### Not Recommended
```bash
# DO NOT use this configuration without proper network-level security controls
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0  # Network-accessible without authentication
MCP_PORT=8000
```

## Disclosing a security issue

The `radkit-mcp-server-community` maintainers take all security issues in the project seriously. Thank you for improving the security of `radkit-mcp-server-community`. We appreciate your dedication to responsible disclosure and will make every effort to acknowledge your contributions.

`radkit-mcp-server-community` leverages GitHub's private vulnerability reporting.

To learn more about this feature and how to submit a vulnerability report, review [GitHub's documentation on private reporting](https://docs.github.com/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability).

Here are some helpful details to include in your report:

- a detailed description of the issue
- the steps required to reproduce the issue
- versions of the project that may be affected by the issue
- if known, any mitigations for the issue

A maintainer will acknowledge the report within three (3) business days, and will send a more detailed response within an additional three (3) business days indicating the next steps in handling your report.

If you've been unable to successfully draft a vulnerability report via GitHub or have not received a response during the alloted response window, please reach out via the [Cisco Open security contact email](mailto:oss-security@cisco.com).

After the initial reply to your report, the maintainers will endeavor to keep you informed of the progress towards a fix and full announcement, and may ask for additional information or guidance.

## Vulnerability management

When the maintainers receive a disclosure report, they will assign it to a primary handler.

This person will coordinate the fix and release process, which involves the following steps:

- confirming the issue
- determining affected versions of the project
- auditing code to find any potential similar problems
- preparing fixes for all releases under maintenance

## Suggesting changes

If you have suggestions on how this process could be improved please submit an issue or pull request.
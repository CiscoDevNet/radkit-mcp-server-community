<h1 align="center">✨🤖 Cisco RADKit MCP Server<br /><br />
<div align="center">
<img src="images/radkit_mcp_logo.png" width="500"/>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&labelColor=555555&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Cisco-1BA0D7?style=flat&logo=cisco&labelColor=555555&logoColor=white" alt="Cisco"/>
  <a href="https://gofastmcp.com/getting-started/welcome"><img src="https://img.shields.io/badge/FastMCP-A259E6?style=flat&labelColor=555555&logo=rocket&logoColor=white"/></a>
</div></h1>

<div align="center">
A <strong>stand-alone MCP server</strong> built with <a href="https://github.com/modelcontextprotocol/fastmcp"><strong>FastMCP</strong></a> that exposes key functionalities of the <a href="https://radkit.cisco.com/"><strong>Cisco RADKit</strong></a> SDK as MCP tools.  
</br>It is designed to be connected to any <strong>MCP client</strong> and <strong>LLM</strong> of your choice, enabling intelligent interaction with network devices through Cisco RADKit.
<br /><br />
</div>

> **Disclaimer**: This MCP Server is not an official Cisco product. It was developed for experimentation and learning purposes.

## 🚀 Overview

This MCP server acts as a lightweight middleware layer between the **Cisco RADKit** service and an **MCP-compatible client**.  
It allows the LLM to inspect and interact with devices onboarded in the RADKit inventory, fetch device attributes, and even execute CLI commands — all through structured MCP tools.

Currently, the implementation supports **stdio transport only** due to dependency incompatibilities between the `radkit` SDK and the `fastmcp` SDK.  
This limitation will be lifted in future releases of the `radkit` SDK.

## ⚙️ Features

- 🔌 **Plug-and-play MCP server** — works with any MCP-compatible client.  
- 🔍 **Inventory discovery** — list all onboarded network devices.  
- 🧠 **Device introspection** — fetch device attributes and capabilities.  
- 🖥️ **Command execution** — run CLI commands on network devices.  
- 📦 **Fully type-hinted tools** for clarity and extensibility.

## 🧰 Exposed MCP Tools

| Tool Name | Description | Inputs | Returns | Use Case |
|------------|--------------|---------|----------|-----------|
| **`get_device_inventory_names()`** | Returns a string containing the names of devices onboarded in the Cisco RADKit inventory. | *None* | `str`: List of onboarded devices (e.g. `{"p0-2e", "p1-2e"}`) | Use this first when the user asks about "devices", "network", or "all devices". |
| **`get_device_attributes(target_device: str)`** | Returns detailed information about a specific device in JSON format. | `target_device (str)`: Target device name. | `str`: JSON with attributes including name, host, type, configs, SNMP/NETCONF status, capabilities, etc. | Use this when the user asks about a specific device. |
| **`exec_cli_command_in_device(target_device: str, cli_command: str)`** | Executes a CLI command on a target device and returns the raw text result. | `target_device (str)`: Device name.<br>`cli_command (str)`: CLI command to execute. | `str`: Raw output of the executed command. | Use this only if info is unavailable in `get_device_attributes()` or when explicitly asked to “run” or “execute” a command. |

## 🧩 Requirements

- Python 3.10+
- Active Cisco RADKit service
- At least one read-only/RW user onboarded in the Cisco RADKit service

For more information about setting up a Cisco RADKit service, visit [this link](https://radkit.cisco.com/#Start).

## 🛠️ Installation

Clone the repository in your deployment environment.
```bash
git clone https://github.com/ponchotitlan/radkit-mcp-server.git
cd radkit-mcp-server
```

## ⚙️ Setup

Execute the included assistant script in a terminal based on your type of host OS:

🐧🍎 Linux/MacOS:
```bash
chmod +x setup.sh
```
```bash
bash setup.sh
```

🪟 Windows:
```bash
setup.bat
```

The assistant will first create a virtual environment folder **radkit-mcp-server/.venv/** with all the python libraries required. Afterwards, it will trigger the following assistant:

```bash
╭─────────────────────────────────────────╮
│ 🚀 Cisco RADKit MCP Server Utility Tool │
╰─────────────────────────────────────────╯
? Choose an option: (Use arrow keys)
 » 1. 👾 Onboard user to non-interactive Cisco RADKit authentication
   2. 📚 Generate .env file for Cisco RADKit MCP server
   Exit
```

### 👾 1. Non-interactive Cisco RADKit authentication setup

The MCP server makes use of certificate login to avoid asking for Web UI authentication every time a tool is used. For that, the certificates need to be generated in the host. Select the first option and follow the instructions.

```bash
╭─────────────────────────────────────────╮
│ 🚀 Cisco RADKit MCP Server Utility Tool │
╰─────────────────────────────────────────╯
? Choose an option: 1. 👾 Onboard user to non-interactive Cisco RADKit authentication
? Enter Cisco RADKit username: ponchotitlan@cisco.com
╭───────────────────────────────────────────────────────────────────╮
│ Starting Cisco RADKit onboarding for user: ponchotitlan@cisco.com │
╰───────────────────────────────────────────────────────────────────╯

A browser window was opened to continue the authentication process. Please follow the instructions there.

Authentication result received.
New private key password: ***********
Confirm: ***********
The private key is a very sensitive piece of information. DO NOT SHARE UNDER ANY CIRCUMSTANCES, and use a very strong passphrase. Please consult the documentation for more details.
<frozen radkit_client.async_.client>:891: UserWarning: The private key is a very sensitive piece of information. DO NOT SHARE UNDER ANY CIRCUMSTANCES, and use a very strong passphrase. Please consult the documentation for more details.
```
**Take note of the password provided, as it will be needed for the 2nd option!**</br>
Now, select the second option:

### 📚 2. Generate .env file

Provide the information requested. The password is the one just setup in the first option.

```bash
? Choose an option: 2. 📚 Generate .env file for Cisco RADKit MCP server
╭───────────────────────────────────────────────────────────────────────────────╮
│ Warning: Make sure Cisco RADKit certificates for this username already exist. │
│ If not, run the onboarding process first using option 1.                      │
╰───────────────────────────────────────────────────────────────────────────────╯
? Enter Cisco RADKit username: ponchotitlan@cisco.com
? Enter Cisco RADKit service code: aaaa-bbbb-cccc
? Enter non-interactive authentication password: ***********
╭──────────────────────────────────────╮
│ ✅ .env file generated successfully! │
│ Saved as .env                        │
╰──────────────────────────────────────╯
```

The file **radkit-mcp-server/.env** is generated with environment variables that the MCP Server needs.</br></br>
✅ **Your MCP server is ready for use!**

## ⚡️ Usage example: Claude Desktop

The Claude Desktop application provides an environment which integrates the Claude LLM and a rich MCP Client compatible with this MCP Server.

To get started, download the [Claude Desktop app](https://claude.ai/download) for your host OS, and choose the LLM usage plan that best fits your needs.

Afterwards, edit the **radkit-mcp-server/claude_desktop_config.json** file included in this repository to point to the **absolute paths** of your _.venv_ and _mcp_server.py_ files:

```json
{
  "mcpServers": {
    "radkit-mcp-server": {
      "command": "/Users/ponchotitlan/Documents/radkit-mcp-server-community/.venv/bin/python",
      "args": [
        "/Users/ponchotitlan/Documents/radkit-mcp-server-community/mcp_server.py"
      ],
      "description": "Cisco RADKit MCP Server - Community"
    }
  }
}
```

Then, copy this file to the location of your Claude Desktop application' configurations. The directory varies depending on your host OS:

🍎 MacOS:
```bash
cp claude_desktop_config.json ~/Library/Application\ Support/Claude 
```

🪟 Windows:
```bash
cp claude_desktop_config.json %APPDATA%\Claude\
```

🐧 Linux:
```bash
cp claude_desktop_config.json ~/.config/Claude/
```

Now, restart your Claude Desktop app. Afterwards, if you navigate to **Configurations/Developer/**, you should see the MCP Server up and running:

<div align="center">
  <img src="images/claude_mcp_okAsset 1.png" width="500"/>
</div>

### ✨ Prompt examples

**📚 Show the inventory of your Cisco RADKit service**</br>
One of the MCP server tools provides a list of device names.
<div align="center">
  <img src="images/radkit_mcp_demo_1_inventory.gif"/>
</div>

</br>**🎰 Ask specific questions about a device**</br>
Another MCP server tool provides information of the device if available directly in the Cisco RADKit SDK.
<div align="center">
  <img src="images/radkit_demo_2_device_type.gif"/>
</div>

</br>Otherwise, a command is executed in the device via a MCP server tool to get the information required.
<div align="center">
  <img src="images/radkit_demo_3_interfaces.gif"/>
</div>

</br>**🗺️ Complex querying using networking data**</br>
The LLM can use the information from multiple data network queries to build, for example, a topology diagram.
<div align="center">
  <img src="images/radkit_demo_4_topology.gif"/>
</div>

</br>This diagram can be later refined with more information from the network as required.
<div align="center">
  <img src="images/radit_demo_5_enhanced_topology.gif"/>
</div>

</br>**⬇️ Push configurations**</br>
Not everything is query information! **If the Cisco RADKit user onboarded in the MCP server is enabled with Write privileges**, commit operations can take place.
<div align="center">
  <img src="images/radkit_demo_6_config_commit.gif"/>
</div>

</br>These are just some examples of what can be done with this MCP server!

---

<div align="center"><br />
    Made with ☕️ by Poncho Sandoval - <code>Developer Advocate 🥑 @ DevNet - Cisco Systems 🇵🇹</code><br /><br />
    <a href="mailto:alfsando@cisco.com?subject=Question%20about%20[RADKIT%20MCP]&body=Hello,%0A%0AI%20have%20a%20question%20regarding%20your%20project.%0A%0AThanks!">
        <img src="https://img.shields.io/badge/Contact%20me!-blue?style=flat&logo=gmail&labelColor=555555&logoColor=white" alt="Contact Me via Email!"/>
    </a>
    <a href="https://github.com/ponchotitlan/radkit-mcp-server/issues/new">
      <img src="https://img.shields.io/badge/Open%20Issue-2088FF?style=flat&logo=github&labelColor=555555&logoColor=white" alt="Open an Issue"/>
    </a>
    <a href="https://github.com/ponchotitlan/radkit-mcp-server/fork">
      <img src="https://img.shields.io/badge/Fork%20Repository-000000?style=flat&logo=github&labelColor=555555&logoColor=white" alt="Fork Repository"/>
    </a>
</div>

# godMCP - MCP Server Creator and Manager

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13+-green.svg)](https://github.com/jlowin/fastmcp)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)

**godMCP** is a powerful Model Context Protocol (MCP) server that enables you to create, manage, and deploy custom MCP servers with ease. Think of it as a meta-server that helps you build other MCP servers.

> 🎯 **Perfect for:** AI developers, automation enthusiasts, and anyone who wants to extend their MCP-enabled tools with custom functionality.

## Features

- 🚀 **Create MCP Servers** - Generate complete, production-ready MCP servers with custom tools
- 🔧 **Tool Implementation** - Provide full implementations or stubs for incremental development
- 📝 **Configuration Management** - Automatically register servers in your MCP configuration
- 🔄 **Update Tools** - Modify tool implementations after server creation
- 🎯 **Multi-Client Support** - Works with Kiro, Claude Desktop, Cursor, and other MCP clients
- ✅ **Proper Indentation** - Generates syntactically correct Python code
- 🌍 **Environment-Based Config** - Explicit control over where servers are registered

## Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Creating a Server](#creating-a-server)
  - [Updating Tool Implementation](#updating-tool-implementation)
  - [Managing Configuration](#managing-configuration)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Clone and Setup

```bash
git clone <repository-url>
cd god-mcp
```

## Getting Started

### Quick Setup

Add this configuration to your MCP client's config file:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/god-mcp", "god-mcp"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/path/to/this/config/mcp.json", //here newly created mcps will be added
        "USER_MCP_CONFIG_PATH": "/path/to/user/config/mcp.json" //here newly created mcps will be added
      },
      "disabled": false
    }
  }
}
```

**Important:** 
- Replace `/absolute/path/to/god-mcp` with your actual godMCP installation directory
- Set `USER_MCP_CONFIG_PATH` to your user/global mcp config(path of the mcp.json file where you want newly create mcp servers to be added.)
- Set `WORKSPACE_MCP_CONFIG_PATH` to the path of the workspace mcp config file where you want newly create mcp servers to be added.(If provided Workspace mcp config path will be used default.)
- If any one is provided, will be used for creating new mcp server.

### 1. Client-Specific Setup

godMCP works with any MCP-compatible client. Choose your client below for specific configuration paths and instructions:

<details>
<summary><b>Kiro</b></summary>

**Configuration Path:**
- Workspace: `.kiro/settings/mcp.json` (project-specific)
- User: `~/.kiro/settings/mcp.json` (global)

**Setup:**

Edit your workspace or user-level configuration:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/absolute/path/to/workspace/.kiro/settings/mcp.json",
        "USER_MCP_CONFIG_PATH": "/Users/yourusername/.kiro/settings/mcp.json"
      },
      "disabled": false
    }
  }
}
```

**Note:** Set both env vars to the same file where godMCP is configured.

</details>

<details>
<summary><b>Claude Desktop</b></summary>

**Configuration Path:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Setup:**

1. Open Claude Desktop
2. Go to Settings → Developer → Edit Config
3. Add godMCP configuration:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "~/Library/Application Support/Claude/claude_desktop_config.json",
        "USER_MCP_CONFIG_PATH": "~/Library/Application Support/Claude/claude_desktop_config.json"
      },
      "disabled": false
    }
  }
}
```

**Note:** Claude Desktop doesn't have workspace concept, so both env vars point to the same file.

</details>

<details>
<summary><b>Claude Code</b></summary>

**Configuration Path:**
- Project: `.mcp.json` (project root)
- Global: `~/.claude.json`

**Setup via CLI:**

```bash
claude mcp add godMCP
```

**Manual Setup:**

Edit `.mcp.json` or `~/.claude.json`:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/absolute/path/to/project/.mcp.json",
        "USER_MCP_CONFIG_PATH": "/Users/yourusername/.claude.json"
      },
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary><b>Cursor</b></summary>

**Configuration Path:**
- Global: 
  - macOS: `~/Library/Application Support/Cursor/User/settings.json`
  - Windows: `%APPDATA%\Cursor\User\settings.json`
  - Linux: `~/.config/Cursor/User/settings.json`
- Project: `.cursor/mcp.json`

**Setup:**

Edit your configuration file:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/absolute/path/to/project/.cursor/mcp.json",
        "USER_MCP_CONFIG_PATH": "~/Library/Application Support/Cursor/User/settings.json"
      },
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary><b>GitHub Copilot</b></summary>

**Configuration Path:**
- `~/.copilot/config.json` or `mcp-config.json`

**Setup via Command:**

```bash
/mcp add
```

Follow the interactive prompts to add godMCP.

**Manual Setup:**

Edit `~/.copilot/config.json`:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "~/.copilot/config.json",
        "USER_MCP_CONFIG_PATH": "~/.copilot/config.json"
      },
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary><b>Cline (VS Code Extension)</b></summary>

**Configuration Path:**
- `.cline_mcp_settings.json`

**Setup:**

1. Open VS Code
2. Click MCP Servers icon
3. Go to Configure tab
4. Add godMCP configuration:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/absolute/path/to/project/.cline_mcp_settings.json",
        "USER_MCP_CONFIG_PATH": "/absolute/path/to/project/.cline_mcp_settings.json"
      },
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary><b>Windsurf IDE</b></summary>

**Configuration Path:**
- macOS: `~/Library/Application Support/Windsurf/User/settings.json`
- Windows: `%APPDATA%\Windsurf\User\settings.json`
- Linux: `~/.config/Windsurf/User/settings.json`

**Setup:**

1. Open Cascade AI panel
2. Go to MCP Servers
3. Click "Add custom server"
4. Add configuration:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "~/Library/Application Support/Windsurf/User/settings.json",
        "USER_MCP_CONFIG_PATH": "~/Library/Application Support/Windsurf/User/settings.json"
      },
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary><b>Zed IDE</b></summary>

**Configuration Path:**
- `settings.json` with `context_servers` object

**Setup:**

1. Open Agent Panel
2. Go to Settings
3. Click "Add Custom Server"
4. Add configuration:

```json
{
  "context_servers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/path/to/settings.json",
        "USER_MCP_CONFIG_PATH": "/path/to/settings.json"
      }
    }
  }
}
```

</details>

<details>
<summary><b>JetBrains IDEs (IntelliJ, PyCharm, etc.)</b></summary>

**Requirements:**
- Version 2025.2 or later

**Setup:**

1. Go to Settings → Tools → Model Context Protocol
2. Add new MCP server
3. Configure:
   - Command: `uv`
   - Arguments: `run --directory /absolute/path/to/god-mcp god-mcp`
   - Environment Variables:
     - `FASTMCP_LOG_LEVEL=INFO`
     - `WORKSPACE_MCP_CONFIG_PATH=/path/to/config`
     - `USER_MCP_CONFIG_PATH=/path/to/config`

</details>

<details>
<summary><b>PurecodeAI</b></summary>

**Configuration Path:**
- Project-specific or global configuration file

**Setup:**

Add godMCP to your MCP configuration:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/path/to/workspace/config.json",
        "USER_MCP_CONFIG_PATH": "/path/to/user/config.json"
      },
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary><b>Other MCP Clients</b></summary>

For any MCP-compatible client, use the standard configuration format:

```json
{
  "mcpServers": {
    "godMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/god-mcp",
        "god-mcp"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "WORKSPACE_MCP_CONFIG_PATH": "/path/to/workspace/mcp.json",
        "USER_MCP_CONFIG_PATH": "/path/to/user/mcp.json"
      },
      "disabled": false
    }
  }
}
```

**Key Points:**
- Replace `/absolute/path/to/god-mcp` with your actual godMCP directory
- Set `WORKSPACE_MCP_CONFIG_PATH` to your workspace/project config file
- Set `USER_MCP_CONFIG_PATH` to your user/global config file
- Both can point to the same file if your client doesn't support workspace concept

</details>

### 2. Restart Your MCP Client

Restart or reconnect your MCP client to load godMCP.

### 3. Verify Installation

Use the `health_check` tool to verify godMCP is running:

```
Can you check if godMCP is healthy?
```

## Configuration

### Environment Variables

godMCP uses two environment variables to determine where to register created servers:

- **`WORKSPACE_MCP_CONFIG_PATH`**: Path to workspace-level MCP configuration
- **`USER_MCP_CONFIG_PATH`**: Path to user-level MCP configuration

**Important:** Both should typically point to the same file where godMCP itself is configured (the "current scope").

### Configuration Levels

When creating servers, you can specify:

- `config_level="workspace"` - Register in workspace config (default)
- `config_level="user"` - Register in user config
- `target_config_path="/custom/path/mcp.json"` - Explicit path override

### Check Current Configuration

Use the `get_config_info` tool to see your current configuration:

```
Show me the current godMCP configuration
```

## Usage

### Creating a Server

Create a new MCP server with custom tools:

```
Create an MCP server called "calculator" with these operations:
- add: adds two numbers
- subtract: subtracts two numbers
- multiply: multiplies two numbers
- divide: divides two numbers (with zero check)
```

**With Full Implementation:**

```python
create_mcp_server(
    name="calculator",
    description="A calculator with basic arithmetic operations",
    tools=[
        {
            "name": "add",
            "description": "Add two numbers together",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            },
            "implementation": """result = a + b
return {
    "status": "success",
    "result": result,
    "expression": f"{a} + {b} = {result}"
}"""
        }
    ]
)
```

### Updating Tool Implementation

Modify a tool's implementation after creation:

```
Update the calculator's add function to include a timestamp
```

```python
update_tool_implementation(
    server_name="calculator",
    tool_name="add",
    implementation="""from datetime import datetime
result = a + b
return {
    "status": "success",
    "result": result,
    "expression": f"{a} + {b} = {result}",
    "timestamp": datetime.now().isoformat()
}"""
)
```

### Managing Configuration

**Read Configuration:**

```python
read_mcp_json(level="both")  # Read both workspace and user configs
```

**Update Configuration:**

```python
update_mcp_json(
    server_name="my-server",
    server_config={
        "command": "uvx",
        "args": ["my-server"],
        "disabled": false
    },
    level="workspace"
)
```

**Remove Server:**

```python
remove_mcp_server(server_name="calculator")
```

## Available Tools

### Server Creation

- **`create_mcp_server`** - Create a new MCP server with custom tools
  - Parameters: name, description, tools, dependencies, output_dir, register, config_level, target_config_path
  - Returns: Server information including paths and registration status

### Tool Management

- **`update_tool_implementation`** - Update a tool's implementation code
  - Parameters: server_name, tool_name, implementation
  - Returns: Update status and file path

### Configuration Management

- **`read_mcp_json`** - Read MCP configuration files
  - Parameters: level ("workspace", "user", or "both")
  - Returns: Configuration data with metadata

- **`update_mcp_json`** - Add or update a server entry
  - Parameters: server_name, server_config, level
  - Returns: Success confirmation

- **`remove_mcp_server`** - Remove a server from configuration
  - Parameters: server_name
  - Returns: Removal confirmation

- **`get_config_info`** - Get current configuration paths and status
  - Returns: Configuration information including paths, sources, and writability

### Utilities

- **`health_check`** - Verify godMCP is running
  - Returns: Health status information

## Examples

### Example 1: Simple Calculator

```
Create a calculator MCP server with add, subtract, multiply, and divide operations. 
Include proper error handling for division by zero.
```

### Example 2: File Utilities Server

```
Create an MCP server called "file-utils" with these tools:
- read_file: reads a file and returns its content
- write_file: writes content to a file
- list_directory: lists files in a directory
```

### Example 3: Incremental Development

```
1. Create a server with stub implementations:
   "Create a data-processor server with parse_csv and analyze_data tools"

2. Later, implement the tools:
   "Update the parse_csv tool to actually parse CSV files using the csv module"
```

## Troubleshooting

### Server Not Registered in Correct Location

**Problem:** Created servers appear in the wrong mcp.json file.

**Solution:** Ensure environment variables are set correctly:

```json
"env": {
  "WORKSPACE_MCP_CONFIG_PATH": "/correct/path/to/mcp.json",
  "USER_MCP_CONFIG_PATH": "/correct/path/to/mcp.json"
}
```

Use `get_config_info` to verify current paths.

### IndentationError in Generated Code

**Problem:** Generated server has syntax errors.

**Solution:** This should be fixed in the latest version. If you encounter this:
1. Update to the latest godMCP version
2. Reconnect the godMCP server
3. Recreate the server

### Server Not Starting

**Problem:** Created server fails to start.

**Solution:**
1. Check the server's debug log: `.mcp-servers/<server-name>/<server-name>_debug.log`
2. Verify the server directory exists
3. Ensure `uv` is installed and accessible
4. Reconnect the MCP client

### Environment Variables Not Working

**Problem:** godMCP still uses fallback paths.

**Solution:**
1. Verify environment variables are in the correct config file
2. Restart/reconnect your MCP client
3. Use `get_config_info` to confirm variables are loaded

## Development

### Project Structure

```
god-mcp/
├── src/
│   └── god_mcp/
│       ├── __init__.py
│       ├── server.py           # Main FastMCP server
│       ├── config_manager.py   # Configuration file management
│       ├── server_creator.py   # Server generation logic
│       └── models.py           # Data models
├── .mcp-servers/               # Generated servers location
├── pyproject.toml
└── README.md
```

### Running Locally

```bash
cd god-mcp
uv run god-mcp
```

### Generated Server Structure

Each created server has this structure:

```
.mcp-servers/<server-name>/
├── src/
│   └── <package-name>/
│       ├── __init__.py
│       └── server.py
├── pyproject.toml
├── README.md
└── <server-name>_debug.log
```

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on:

- Setting up your development environment
- Code style guidelines
- Submitting pull requests
- Reporting issues

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/godmcp.git
cd godmcp/god-mcp

# Install dependencies
uv sync

# Run locally
uv run god-mcp
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) - A fast, modern framework for building MCP servers
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io) specification
- Thanks to all contributors who help improve godMCP

## Support

- 📖 **Documentation:** Check this README and [CONTRIBUTING.md](CONTRIBUTING.md)
- 🐛 **Bug Reports:** [Open an issue](https://github.com/YOUR_USERNAME/godmcp/issues)
- 💡 **Feature Requests:** [Open an issue](https://github.com/YOUR_USERNAME/godmcp/issues)
- 💬 **Questions:** [Start a discussion](https://github.com/YOUR_USERNAME/godmcp/discussions)

## Roadmap

- [ ] Add support for resource templates
- [ ] Implement prompt management
- [ ] Add server testing utilities
- [ ] Create web UI for server management
- [ ] Support for multiple programming languages
- [ ] Integration with popular AI development tools

---

**Made with ❤️ for the MCP community**

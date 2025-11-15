# MCP Clients: Specifications & Configuration Paths

I've created a comprehensive guide covering MCP specifications and configuration paths for all major MCP clients. Here's what you need to know:

## MCP Specification Foundation

The **Model Context Protocol** uses **JSON-RPC 2.0** for all communications between clients and servers. The protocol version is **2025-06-18** (latest), and it supports three transport types:[1][2][3]

- **stdio**: Local process-to-process communication, ideal for development and desktop deployments
- **HTTP**: Remote server communication across networks
- **SSE (Server-Sent Events)**: Real-time streaming and asynchronous event delivery

## Major MCP Clients & Configuration Paths

### Claude Desktop[4][5][6]
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Setup**: Settings → Developer → Edit Config

### Claude Code[7]
- **Project-level**: `.mcp.json` in project root
- **Global-level**: `~/.claude.json`
- **Enterprise**: `/Library/Application Support/ClaudeCode/managed-mcp.json` (macOS)
- **Commands**: `claude mcp add`, `claude mcp list`

### Cursor IDE[8]
- **macOS**: `~/Library/Application Support/Cursor/User/settings.json`
- **Windows**: `%APPDATA%\Cursor\User\settings.json`
- **Linux**: `~/.config/Cursor/User/settings.json`
- **Local**: `.cursor/mcp.json` (project-specific)

### Cline (VS Code Extension)[9]
- **Config File**: `.cline_mcp_settings.json`
- **Access**: MCP Servers icon → Configure tab
- **Features**: Individual server panels, tool management

### GitHub Copilot[10][11]
- **Path**: `~/.copilot/config.json` or `mcp-config.json`
- **Command**: `/mcp add` (interactive setup)
- **Enterprise**: Supports organization-wide MCP registry URLs and access policies

### Gemini CLI[12]
- **Path**: `~/.config/gemini/settings.json` or project-level `settings.json`
- **Config Key**: Define servers under `"mcp"` key
- **Support**: Local and remote MCP servers

### Windsurf IDE[13]
- **macOS**: `~/Library/Application Support/Windsurf/User/settings.json`
- **Windows**: `%APPDATA%\Windsurf\User\settings.json`
- **Linux**: `~/.config/Windsurf/User/settings.json`
- **UI Setup**: Cascade AI panel → MCP Servers → Add custom server

### Kilocode[14]
- **Config**: `mcp.json` (global or project-level)
- **Setup**: Via Marketplace or manual JSON configuration
- **Scope**: Global or project-specific
- **Requirement**: Node.js must be installed

### OpenCode[15]
- **Config Key**: Under `mcp` key in project configuration
- **Types**: Local (stdio) or Remote (HTTP)
- **Features**: Per-server enable/disable, configurable timeouts (default 5000ms)

### Zed IDE[16][17]
- **Config**: `settings.json` with `context_servers` object
- **Setup**: Agent Panel → Settings → Add Custom Server
- **Support**: Custom command-line executables

### JetBrains IDEs[18]
- **Version**: v2025.2+ (dual-mode: client and server)
- **UI Access**: Settings → Tools → Model Context Protocol
- **Dual Mode**: Connect to external servers or expose IDE as MCP server
- **Auto-Configure**: For Claude Code, Cursor, VS Code, Windsurf

### VS Code[19]
- **Command**: `code --add-mcp server-name command args`
- **Extension API**: `vscode.lm.registerMcpServerDefinitionProvider()`
- **Features**: Extension-based registration, autodiscovery

### Sublime Text[20]
- **Integration**: Via Codex extension with comprehensive MCP support
- **Features**: Per-project configuration, parallel execution

## Standard Configuration Format

All MCP clients use a similar JSON structure:[21]

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "VARIABLE": "value"
      },
      "disabled": false,
      "alwaysAllow": ["tool1", "tool2"]
    }
  }
}
```

## Key Features Across Clients

**Environment Variable Expansion**: `${API_KEY}` or `${API_KEY:-default_value}`[7]

**Scope Management**: Many clients support global, project, and enterprise scopes

**Initialization Handshake**: Clients negotiate protocol version and capabilities during connection[22][23]

**MCP Registryegistry**: Official registry at `registry.modelcontextprotocol.io` launched September 2025[33]
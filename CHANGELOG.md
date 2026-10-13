# Changelog

All notable changes to godMCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Agent-agnostic modernization — October 2026

- Added explicit host selection, eight built-in adapters and configurable JSON/TOML adapters.
- Added a preview-first CLI for bootstrap and installation; preserve unrelated settings, back up configs and detect conflicting changes.
- Separated Python/FastMCP generation from host registration; removed the implicit Kiro fallback.
- Added generated-source syntax checks, configuration redaction, scope-safe removal and protocol tests.
- Documented direct Codex discovery and Pi client invocation checks, including activation limits.
- Added a guided agent skill and architecture/workflow diagrams.

### Earlier development notes

### Added
- Initial release of godMCP
- `create_mcp_server` tool for generating complete MCP server packages
- `update_tool_implementation` tool for modifying tool code after creation
- `read_mcp_json` tool for reading MCP configuration files
- `update_mcp_json` tool for managing MCP server configurations
- `remove_mcp_server` tool for removing servers from configuration
- `health_check` tool for server status verification
- `get_config_info` tool for configuration path information
- Automatic server registration in mcp.json
- Support for custom dependencies in generated servers
- Implementation hints for tool generation
- Comprehensive logging infrastructure
- Multi-client support (Kiro, Claude Desktop, Cursor, etc.)

### Documentation
- Comprehensive README with examples
- CONTRIBUTING.md guide for developers
- MCP clients configuration guide
- Usage documentation with real-world examples

## [0.1.0] - 2024-11-15

### Added
- Initial project structure
- Core server creation functionality
- Configuration management system
- Data models for ServerSpec and ToolSpec
- FastMCP-based server implementation
- Logging infrastructure
- Package generation with proper Python structure

### Features
- Generate local MCP server packages
- Automatic pyproject.toml generation
- README generation for created servers
- Proper Python package structure
- Type hints and validation
- Error handling and logging

---

## Version History

### Version 0.1.0 (Initial Release)
- First public release of godMCP
- Core functionality for creating and managing MCP servers
- Support for FastMCP framework
- Configuration management tools
- Documentation and examples

---

## Upgrade Guide

### From Development to 0.1.0
No upgrade needed - this is the initial release.

---

## Future Plans

See repository issues for proposed work. The [README](README.md) describes current behavior and limits.

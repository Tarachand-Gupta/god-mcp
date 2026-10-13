---
name: god-mcp
description: Create and test MCP servers from API documentation, gather required credentials securely, and install God MCP or generated servers into current, selected, detected, or all supported coding agents. Use for MCP creation and cross-agent installation, including new agent adapters.
---

# God MCP

Use God MCP's tools when connected. Otherwise run `uv run --directory <god-mcp-repository> god-mcp-config` for configuration and `uv run --directory <god-mcp-repository> god-mcp` for the server. The repository is supplied by the user or located in the working project; never invent its absolute path.

## Choose the installation targets

Call `discover_agents`. Separate evidence that an agent is installed from evidence of the current harness. Prefer the explicit `GOD_MCP_AGENT` set by bootstrap. A model name does not identify its harness. If current is unknown, ask which agent to target while continuing API research.

Honor the user's scope: current, named agents, detected agents, or all. Offer installation to other agents when discussing setup. Explicit names work even when detection fails. `all` means every registered adapter, including undetected ones; disclose this set and per-agent failures. It cannot mean every agent that exists. For an unlisted agent, research its official MCP support and add an adapter before claiming compatibility.

Use `god-mcp-config --workspace <project> bootstrap --target <agent> --scope user` to preview God MCP installation. Add `--apply` for an authorized installation. Bootstrap gives each launched server its host identity and working project. For workspace installation, select `--scope workspace`; some desktop clients have only user scope. Do not silently substitute scope.

## Research and collect inputs

Start with the provider's official API documentation or OpenAPI document. Confirm base URL, API version, exact endpoints, auth method, required scopes, request and response schemas, pagination, rate limits, and which operations mutate data. Record source links in the generated package documentation. Prefer existing official MCP servers when they already meet the request.

Ask for the desired operations and missing account/workspace identifiers. If credentials are needed, give the exact environment variable names and provider setup instructions. Ask the user to set credentials locally through their secret manager or launch environment and confirm readiness; do not request raw API keys in chat. Never put keys in source, examples, logs, test fixtures, or tool results. GUI clients may not inherit shell variables; verify presence without revealing values. OAuth and environment interpolation differ by host: consult the selected host's documentation rather than assuming `${NAME}` works everywhere.

Continue writing and testing with mocked API responses while waiting for credentials. Missing credentials are not permission to invent them or claim authenticated tests passed.

## Create and verify

`create_mcp_server` accepts name, description, tool specifications, dependencies, output_dir, register, config_level and targets. Current implementation generates Python/FastMCP packages. MCP interoperability is independent of implementation language; do not claim it generates JavaScript. Each tool has a JSON schema and a Python implementation body. Unsupported language requests need an additional generator, not relabeling Python output.

Use `register=False` while building, or pass the user's intended `targets` when creation should also install. Implement API requests with timeouts, explicit non-success handling and bounded pagination. Validate data before mutation. Avoid retrying non-idempotent writes. Implementation bodies are executable trusted code, not a sandbox. Missing implementations fail instead of pretending to succeed.

Test the generated server through MCP: initialize, list tools, invoke a harmless tool, check the result, and verify invalid-input/auth failures. A generated file or config entry alone is not a passing integration test. For real APIs, use read-only operations unless writes were requested. Never log arguments or responses containing secrets.

## Install and activate

Use `install_mcp_server(server_name, server_config, targets, scope, dry_run=True)` to inspect paths. Apply with `dry_run=False` when the user's request authorizes installation. Preserve other servers/settings. Conflicting entries require an intentional replacement; malformed configuration must be repaired without discarding its contents. Writes create backups and report per-agent outcomes.

Codex uses TOML `mcp_servers`; most supported clients use JSON `mcpServers`; VS Code uses JSON `servers`. Custom JSON/TOML mappings are supplied by `GOD_MCP_AGENTS_FILE` (see repository README). More complex formats need a real adapter, not a guessed path.

Pi with built-in MCP support uses `~/.pi/agent/mcp.json` or trusted-project `.pi/mcp.json`; run `/reload` then `/mcp`. An agent operating inside Pi with its extension API can call `pi.registerMcpServer` for immediate session registration; that does not persist installation. Older Pi versions and replacement MCP extensions may behave differently. Verify the installed version's capabilities.

For each target report: generated, configured, connected, and tool call verified, only as supported by evidence. Give the actual reconnect/reload step where hot loading is unavailable. Do not claim the current chat has new tools just because the next session's config is written.

Install this skill by copying the complete `god-mcp` folder into the chosen host's supported skills directory (for example `~/.agents/skills/god-mcp` for Codex or `~/.pi/agent/skills/god-mcp` for Pi). Verify that host's discovery rules first. Do not install skills into unrelated agents merely because they were detected.

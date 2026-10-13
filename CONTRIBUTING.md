# Contributing to God MCP

## Local setup

Use Python 3.10+ and uv. Clone this repository or your fork, then run:

```sh
uv sync --locked --extra dev
uv run --locked pytest -q
uv run --locked ruff check src tests scripts
```

The MCP server uses stdio. `uv run god-mcp` waits for a client connection; it is not an HTTP page or an interactive shell. Use `uv run god-mcp-config --help` for the separate configuration CLI.

## Code map

| File | Responsibility |
|---|---|
| `src/god_mcp/server.py` | MCP tools and entry point |
| `src/god_mcp/server_creator.py` | Generated Python packages and tool updates |
| `src/god_mcp/models.py` | Server/tool specifications |
| `src/god_mcp/agents.py` | Host discovery, adapters and configuration writes |
| `src/god_mcp/config_manager.py` | Scope selection and compatibility helpers |
| `src/god_mcp/cli.py` | Headless discovery, bootstrap and installation |
| `tests/test_agents.py` | Temporary-file adapter and configuration tests |
| `tests/test_protocol.py` | MCP initialization, discovery and invocation |
| `scripts/smoke_harnesses.py` | Optional isolated Codex/Pi checks |

## Making changes

Keep generation independent of a particular model, provider or agent. For new adapters, verify the host's actual configuration schema and activation behavior; keep claims about file generation separate from live tool invocation.

Add focused tests for changed behavior. Configuration tests must use temporary directories and preserve unrelated settings. Test conflict handling and unsupported scopes as well as the successful path. Never modify a contributor's live agent configuration from a test.

Generated tool bodies are executable Python. Keep syntax checks, reject invalid identifiers and avoid logging tool arguments or credentials. Do not describe the generator as a sandbox or full JSON Schema validator.

Run the checks above and `git diff --check` before opening a pull request. Explain the problem, resulting behavior and checks performed. If dependencies change, update `uv.lock`.

## Optional host checks

With the tested Codex and Pi distributions installed:

```sh
uv run --locked python scripts/smoke_harnesses.py
```

This uses temporary host configuration and does not call a model. See [VALIDATION.md](VALIDATION.md) for versions and limitations. A passing adapter test alone is not proof of host activation.

## Reporting an issue

Include reproduction steps, expected/actual behavior, OS, Python version and agent version. Share only a minimal redacted configuration or log excerpt; never attach credentials, full user configuration or private backups.

Contributions are covered by the repository's [MIT license](LICENSE).

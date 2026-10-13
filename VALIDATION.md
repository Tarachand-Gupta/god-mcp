# Validation — 14 October 2026

Re-ran the checks below on 14 October 2026 from the local source checkout. The checks use temporary agent configuration and leave live user configuration unchanged.

- `uv run --locked pytest -q`: **12 passed**. Covers JSON/TOML preservation, backups, idempotence, conflicts, malformed configs, explicit and custom targets, partial failures, redaction, scope-safe removal, generated-server MCP calls, and God MCP's module entrypoint and creation tool.
- `uv run --locked ruff check src tests scripts`: passed.
- Skill creator's `quick_validate.py skills/god-mcp`: passed using the project environment.
- `git diff --check`: passed.
- `uv run --locked python scripts/smoke_harnesses.py`: passed with temporary agent configuration, without model calls or changes to live user agent configs.

## Harness evidence

**Codex 0.160.1:** its CLI accepted the generated calculator config. Its native app server initialized the generated MCP server and discovered tools via `mcpServerStatus/list`. This does not claim a model-selected tool call or hot installation in the existing desktop chat.

**Pi @earendil-works/pi-coding-agent 1.2.0:** native `pi mcp list --json` connected to both God MCP and the generated calculator. Pi's bundled `@earendil-works/pi-mcp` client initialized the calculator, listed `add`, called `add(19,23)`, and received `42`.

**Delegation limitation:** the requested Harness Bridge Pi model task timed out during the prompt stage with `outcomeUnknown: true`; its queued follow-up was cancelled. It was not resubmitted. The direct checks above are independent of that failed model delegation. A future model-driven test requires checking the worker/provider service first.

Other built-in agents have configuration adapters, but were not launched for live compatibility tests. New agents can be registered through a JSON/TOML adapter description; incompatible entry schemas require a code adapter. Current generation remains Python/FastMCP. Session activation still depends on each host's reload, reconnect, trust, and approval mechanisms. Credentialed external APIs were not tested because no particular provider or credential was requested.

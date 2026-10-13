# MCP client installation

See [the maintained adapter table and setup guide](README.md#agent-adapters) and the [God MCP skill](skills/god-mcp/SKILL.md). The previous client examples mixed settings-file formats; the adapter implementation is now the source of truth for supported paths and schemas.

Preview with `god-mcp-config ... bootstrap`, apply with `--apply`, then verify the connection in the selected client. Configuration and active tool availability are separate outcomes.

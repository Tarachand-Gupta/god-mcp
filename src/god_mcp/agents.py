"""Explicit, extensible MCP client adapters. Discovery is evidence, not permission."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

import tomlkit


@dataclass(frozen=True)
class Agent:
    id: str
    user_path: str
    workspace_path: str | None
    key: str = "mcpServers"
    format: str = "json"
    command: str | None = None
    note: str = "Reconnect or restart the MCP client to load changes."


BUILTINS = [
    Agent("codex", "~/.codex/config.toml", ".codex/config.toml", "mcp_servers", "toml", "codex"),
    Agent("claude-code", "~/.claude.json", ".mcp.json", command="claude"),
    Agent("cursor", "~/.cursor/mcp.json", ".cursor/mcp.json", command="cursor"),
    Agent("kiro", "~/.kiro/settings/mcp.json", ".kiro/settings/mcp.json", command="kiro"),
    Agent("vscode", "~/.config/Code/User/mcp.json", ".vscode/mcp.json", "servers", command="code"),
    Agent("windsurf", "~/.codeium/windsurf/mcp_config.json", None, command="windsurf"),
    Agent(
        "pi",
        "~/.pi/agent/mcp.json",
        ".pi/mcp.json",
        note="Requires Pi with built-in MCP support (verified with @earendil-works/pi-coding-agent 1.2.0). Run /reload, then /mcp.",
        command="pi",
    ),
]


class AgentRegistry:
    def __init__(self, workspace=None, home=None, environ=None, custom=None):
        self.workspace = Path(workspace or os.getcwd()).resolve()
        self.home = Path(home or Path.home()).resolve()
        self.env = os.environ if environ is None else environ
        self.agents = {a.id: a for a in BUILTINS}
        import sys

        if sys.platform == "darwin":
            self.agents["claude-desktop"] = Agent(
                "claude-desktop",
                "~/Library/Application Support/Claude/claude_desktop_config.json",
                None,
            )
            self.agents["vscode"] = Agent(
                "vscode",
                "~/Library/Application Support/Code/User/mcp.json",
                ".vscode/mcp.json",
                "servers",
                command="code",
            )
        elif sys.platform == "win32":
            base = self.env.get("APPDATA", str(self.home / "AppData/Roaming"))
            self.agents["claude-desktop"] = Agent(
                "claude-desktop", str(Path(base) / "Claude/claude_desktop_config.json"), None
            )
            self.agents["vscode"] = Agent(
                "vscode",
                str(Path(base) / "Code/User/mcp.json"),
                ".vscode/mcp.json",
                "servers",
                command="code",
            )
        if self.env.get("CODEX_HOME"):
            from dataclasses import replace

            self.agents["codex"] = replace(
                self.agents["codex"], user_path=str(Path(self.env["CODEX_HOME"]) / "config.toml")
            )
        path = custom or self.env.get("GOD_MCP_AGENTS_FILE")
        if path:
            for entry in json.loads(Path(path).expanduser().read_text()):
                agent = Agent(**entry)
                if agent.format not in ("json", "toml") or not agent.id or not agent.key:
                    raise ValueError("Custom adapters require id, key and json/toml format")
                self.agents[agent.id] = agent

    def current(self):
        explicit = self.env.get("GOD_MCP_AGENT")
        if explicit:
            if explicit not in self.agents:
                raise ValueError(f"Unknown GOD_MCP_AGENT: {explicit}")
            return explicit
        signals = []
        if self.env.get("CODEX_THREAD_ID") or self.env.get("CODEX_SESSION_ID"):
            signals.append("codex")
        if self.env.get("CLAUDECODE"):
            signals.append("claude-code")
        # Installed agents and model/provider names do not identify the active harness.
        return signals[0] if len(signals) == 1 else None

    def path(self, agent_id, scope="workspace"):
        if scope not in ("workspace", "user"):
            raise ValueError("scope must be workspace or user")
        agent = self.agents[agent_id]
        value = agent.workspace_path if scope == "workspace" else agent.user_path
        if not value:
            raise ValueError(f"{agent_id} has no {scope} configuration; select user scope")
        if value.startswith("~/"):
            return self.home / value[2:]
        path = Path(value)
        return path if path.is_absolute() else self.workspace / path

    def discover(self):
        current = self.current()
        results = []
        for agent in self.agents.values():
            paths = {
                s: str(self.path(agent.id, s))
                for s in ("user", "workspace")
                if s == "user" or agent.workspace_path
            }
            evidence = [p for p in paths.values() if Path(p).exists()]
            binary = shutil.which(agent.command) if agent.command else None
            results.append(
                {
                    "id": agent.id,
                    "detected": bool(evidence or binary or agent.id == current),
                    "current": agent.id == current,
                    "paths": paths,
                    "evidence": evidence + ([binary] if binary else []),
                    "note": agent.note,
                }
            )
        return results

    def targets(self, targets):
        targets = targets or ["current"]
        if isinstance(targets, str):
            targets = [targets]
        selected = []
        for target in targets:
            if target == "all":
                selected.extend(self.agents)
            elif target == "detected":
                selected.extend(a["id"] for a in self.discover() if a["detected"])
            elif target == "current":
                current = self.current()
                if not current:
                    raise ValueError(
                        "Current agent is unknown. Set GOD_MCP_AGENT or specify targets explicitly."
                    )
                selected.append(current)
            elif target in self.agents:
                selected.append(target)
            else:
                raise ValueError(f"Unknown agent {target!r}. Add it through GOD_MCP_AGENTS_FILE.")
        return list(dict.fromkeys(selected))

    def install(self, name, config, targets=None, scope="workspace", dry_run=True, replace=False):
        validate_config(config)
        results = []
        for target in self.targets(targets):
            agent = self.agents[target]
            try:
                path = self.path(target, scope)
                entry = {k: v for k, v in config.items() if k in ("command", "args", "env", "url")}
                if target == "vscode":
                    entry["type"] = "http" if "url" in entry else "stdio"
                elif target in ("claude-code", "cursor") and "url" in entry:
                    entry["type"] = "http"
                result = write_entry(path, agent.key, name, entry, agent.format, dry_run, replace)
                results.append(
                    {
                        "agent": target,
                        **result,
                        "activation": "not_verified",
                        "next_step": agent.note,
                    }
                )
            except (ValueError, OSError, KeyError) as exc:
                results.append({"agent": target, "status": "error", "error": str(exc)})
        return {
            "success": bool(results) and all(r["status"] != "error" for r in results),
            "results": results,
            "dry_run": dry_run,
        }


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Server config must be an object")
    unknown = set(config) - {"command", "args", "env", "url"}
    if unknown:
        raise ValueError("Unsupported portable config fields: " + ", ".join(sorted(unknown)))
    if ("command" in config) == ("url" in config):
        raise ValueError("Provide exactly one of command (stdio) or url (HTTP)")
    field = "command" if "command" in config else "url"
    if not isinstance(config[field], str) or not config[field].strip():
        raise ValueError(f"{field} must be a nonempty string")
    if field == "url" and not config[field].startswith(("https://", "http://")):
        raise ValueError("url must use HTTP or HTTPS")
    if not isinstance(config.get("args", []), list) or any(
        not isinstance(a, str) for a in config.get("args", [])
    ):
        raise ValueError("args must be a list of strings")
    if not isinstance(config.get("env", {}), dict) or any(
        not isinstance(k, str) or not isinstance(v, str) for k, v in config.get("env", {}).items()
    ):
        raise ValueError("env must map strings to strings")


def write_entry(path, key, name, config, format="json", dry_run=True, replace=False, remove=False):
    """Preserve unrelated settings and TOML comments; refuse silent overwrites."""
    path = Path(path).expanduser().resolve()
    if not name or not isinstance(name, str):
        raise ValueError("Server name is required")
    before = path.read_bytes() if path.exists() else None
    try:
        data = (
            (tomlkit.parse(before.decode()) if format == "toml" else json.loads(before))
            if before
            else {}
        )
        if not isinstance(data, dict) or not isinstance(data.get(key, {}), dict):
            raise ValueError("Expected configuration object and server mapping")
        servers = data.setdefault(key, {})
        existing = servers.get(name)
        if remove and existing is None:
            return {"status": "unchanged", "path": str(path)}
        if not remove and existing == config:
            return {"status": "unchanged", "path": str(path)}
        if existing is not None and not replace and not remove:
            raise ValueError(
                f"Server {name!r} already exists; use replace only for an intentional update"
            )
        if remove:
            del servers[name]
        else:
            servers[name] = config
        content = tomlkit.dumps(data) if format == "toml" else json.dumps(data, indent=2) + "\n"
    except Exception as exc:
        raise ValueError(
            f"Cannot update config ({type(exc).__name__}); existing file was preserved"
        ) from exc
    if dry_run:
        return {"status": "planned", "path": str(path)}
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".god-mcp.lock")
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError(
            "Another God MCP write is in progress; inspect the lock before retrying"
        ) from exc
    backup = None
    temp = None
    try:
        os.close(lock_fd)
        now = path.read_bytes() if path.exists() else None
        if now != before:
            raise ValueError("Config changed during update; retry after reviewing it")
        if before is not None:
            backup = path.with_name(path.name + ".god-mcp-" + uuid.uuid4().hex + ".bak")
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(before)
        fd, temp = tempfile.mkstemp(prefix=".god-mcp-", dir=path.parent)
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp and Path(temp).exists():
            Path(temp).unlink()
        lock.unlink()
    return {"status": "configured", "path": str(path), "backup": str(backup) if backup else None}

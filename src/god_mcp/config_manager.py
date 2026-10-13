"""Compatibility facade for explicitly selected MCP configuration scopes."""

import json
import os
from pathlib import Path

import tomlkit
from god_mcp.agents import AgentRegistry, validate_config, write_entry


class ConfigManager:
    def __init__(self, workspace_dir=None):
        self.registry = AgentRegistry(workspace=workspace_dir)

    def _path(self, level):
        explicit = os.getenv(f"{level.upper()}_MCP_CONFIG_PATH")
        if explicit:
            return Path(explicit).expanduser().resolve()
        current = self.registry.current()
        if not current:
            raise ValueError(
                "Select GOD_MCP_AGENT or set an explicit MCP config path; no agent is assumed"
            )
        return self.registry.path(current, level)

    def get_workspace_config_path(self):
        return self._path("workspace")

    def get_user_config_path(self):
        return self._path("user")

    def _key(self, path):
        if path.suffix == ".toml":
            return "mcp_servers"
        current = self.registry.current()
        return self.registry.agents[current].key if current and current != "codex" else "mcpServers"

    def _read(self, level):
        path = self._path(level)
        data = (
            (
                tomlkit.parse(path.read_text())
                if path.suffix == ".toml"
                else json.loads(path.read_text())
            )
            if path.exists()
            else {}
        )
        return {"mcpServers": dict(data.get(self._key(path), {}))}

    def read_workspace_config(self):
        return self._read("workspace")

    def read_user_config(self):
        return self._read("user")

    def get_merged_config(self):
        user = self.read_user_config()["mcpServers"]
        workspace = self.read_workspace_config()["mcpServers"]
        return {
            "mcpServers": {**user, **workspace},
            "_metadata": {
                "userConfigPath": str(self._path("user")),
                "workspaceConfigPath": str(self._path("workspace")),
                "userServerCount": len(user),
                "workspaceServerCount": len(workspace),
                "totalServerCount": len(user.keys() | workspace.keys()),
            },
        }

    def validate_server_config(self, config):
        validate_config(config)
        return True

    def add_server(self, name, config, level="workspace"):
        validate_config(config)
        explicit = os.getenv(f"{level.upper()}_MCP_CONFIG_PATH")
        if explicit:
            path = self._path(level)
            return write_entry(
                path,
                self._key(path),
                name,
                config,
                "toml" if path.suffix == ".toml" else "json",
                False,
            )
        result = self.registry.install(name, config, ["current"], level, False)
        if not result["success"]:
            raise ValueError(str(result["results"]))
        return result

    def remove_server(self, name, level="workspace"):
        path = self._path(level)
        result = write_entry(
            path,
            self._key(path),
            name,
            None,
            "toml" if path.suffix == ".toml" else "json",
            False,
            remove=True,
        )
        return {
            "workspace": level == "workspace" and result["status"] == "configured",
            "user": level == "user" and result["status"] == "configured",
        }

"""Generate portable Python MCP servers, independently of their host agent."""

import ast
import json
import keyword
from pathlib import Path
import textwrap

from god_mcp.config_manager import ConfigManager
from god_mcp.models import ServerSpec, ToolSpec
from god_mcp.agents import write_entry


class ServerCreator:
    def __init__(self, base_output_dir=None, config_manager=None):
        self.base_output_dir = Path(base_output_dir or Path.cwd() / ".mcp-servers").resolve()
        self.config_manager = config_manager or ConfigManager()

    def generate_tool_code(self, tool: ToolSpec):
        params = []
        schema = tool.parameters
        required = schema.get("required", [])
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }
        for name, info in schema.get("properties", {}).items():
            if not name.isidentifier() or keyword.iskeyword(name):
                raise ValueError(f"Invalid Python parameter: {name}")
            typ = type_map.get(info.get("type"), "Any")
            params.append(
                f"{name}: {typ}"
                if name in required
                else f"{name}: Optional[{typ}] = {repr(info.get('default'))}"
            )
        # Keyword-only parameters support optional properties before required ones.
        signature = "*, " + ", ".join(params) if params else ""
        implementation = (
            tool.implementation_hint or 'raise NotImplementedError("Tool implementation required")'
        )
        return (
            f"\n@mcp.tool()\ndef {tool.name}({signature}):\n    {tool.description!r}\n"
            + textwrap.indent(textwrap.dedent(implementation).strip(), "    ")
            + "\n"
        )

    def create_server(
        self,
        spec: ServerSpec,
        register=True,
        config_level="workspace",
        target_config_path=None,
        targets=None,
    ):
        base = (
            Path(spec.output_dir).expanduser().resolve()
            if spec.output_dir
            else self.base_output_dir
        )
        server_dir = base / spec.name
        if server_dir.exists():
            return {
                "success": False,
                "error": "Server directory already exists; update it explicitly",
                "serverDir": str(server_dir),
            }
        package = spec.get_package_name()
        try:
            code = (
                "from typing import Any, Optional\nfrom fastmcp import FastMCP\n\n"
                + f"mcp = FastMCP({spec.name!r})\n"
            )
            code += "".join(self.generate_tool_code(t) for t in spec.tools)
            code += '\ndef main():\n    mcp.run()\n\nif __name__ == "__main__":\n    main()\n'
            ast.parse(code)
            pyproject = "\n".join(
                [
                    "[build-system]",
                    'requires = ["hatchling"]',
                    'build-backend = "hatchling.build"',
                    "",
                    "[project]",
                    f"name = {json.dumps(spec.name)}",
                    'version = "0.1.0"',
                    f"description = {json.dumps(spec.description)}",
                    'requires-python = ">=3.10"',
                    f"dependencies = {json.dumps(spec.get_all_dependencies())}",
                    "",
                    "[project.scripts]",
                    f'{json.dumps(spec.name)} = "{package}.server:main"',
                    "",
                    "[tool.hatch.build.targets.wheel]",
                    f'packages = ["src/{package}"]',
                    "",
                ]
            )
            package_dir = server_dir / "src" / package
            package_dir.mkdir(parents=True, exist_ok=False)
            (package_dir / "__init__.py").write_text("")
            server_file = package_dir / "server.py"
            server_file.write_text(code)
            (server_dir / "pyproject.toml").write_text(pyproject)
            config = {"command": "uv", "args": ["run", "--directory", str(server_dir), spec.name]}
            (server_dir / "mcp.json").write_text(
                json.dumps({"mcpServers": {spec.name: config}}, indent=2) + "\n"
            )
            (server_dir / "README.md").write_text(
                f"# {spec.name}\n\n{spec.description}\n\nRun locally: `uv run --directory {str(server_dir)!r} {spec.name}`.\n\nThis package is local, not published to PyPI. Use God MCP's install_mcp_server to register it with selected agents. mcp.json is a portable descriptor, not proof of activation.\n\nTool implementations are trusted executable code. Configure API credentials through the launching environment, never source code. Reconnect your client after changes.\n"
            )
            result = {
                "success": True,
                "serverName": spec.name,
                "packageName": package,
                "serverDir": str(server_dir),
                "files": {
                    "server": str(server_file),
                    "pyproject": str(server_dir / "pyproject.toml"),
                    "readme": str(server_dir / "README.md"),
                },
                "toolCount": len(spec.tools),
                "tools": [t.name for t in spec.tools],
                "serverConfig": config,
            }
            if register:
                try:
                    if targets:
                        registration = self.config_manager.registry.install(
                            spec.name, config, targets, config_level, False
                        )
                    elif target_config_path:
                        path = Path(target_config_path)
                        registration = write_entry(
                            path,
                            "mcp_servers" if path.suffix == ".toml" else "mcpServers",
                            spec.name,
                            config,
                            "toml" if path.suffix == ".toml" else "json",
                            False,
                        )
                    else:
                        registration = self.config_manager.add_server(
                            spec.name, config, config_level
                        )
                    result["registration"] = registration
                    result["registered"] = registration.get(
                        "success", registration.get("status") in ("configured", "unchanged")
                    )
                except (ValueError, OSError) as exc:
                    result["registered"] = False
                    result["registration"] = {"success": False, "error": str(exc)}
            return result
        except (ValueError, SyntaxError, OSError) as exc:
            return {"success": False, "error": str(exc), "serverName": spec.name}

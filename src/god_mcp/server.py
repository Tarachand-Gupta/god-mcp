"""
Main FastMCP server entry point for godMCP.
"""

import logging
import os
from pathlib import Path
from typing import Literal, Optional

from fastmcp import FastMCP

from god_mcp.config_manager import ConfigManager
from god_mcp.server_creator import ServerCreator
from god_mcp.models import ServerSpec, ToolSpec

# Protocol stdout is reserved for MCP; never log credentials or tool arguments.
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("godMCP")

# Initialize FastMCP server
mcp = FastMCP("godMCP")

# Initialize ConfigManager and ServerCreator
config_manager = ConfigManager(workspace_dir=os.getenv("GOD_MCP_WORKSPACE"))
server_creator = ServerCreator(
    base_output_dir=Path(os.getenv("GOD_MCP_WORKSPACE", os.getcwd())) / ".mcp-servers",
    config_manager=config_manager,
)


def redact_config(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower() in {"env", "headers", "http_headers", "args", "url"}
            or any(part in key.lower() for part in ("token", "secret", "password", "api_key"))
            else redact_config(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_config(item) for item in value]
    return value


@mcp.tool()
def get_config_info() -> dict:
    """
    Get information about current MCP configuration paths being used.

    Shows which configuration files are being used for workspace and user levels,
    whether they exist, and their source (environment variable or fallback).

    Returns:
        dict: Configuration information including paths, existence, and sources
    """
    paths = {}
    for scope in ("workspace", "user"):
        try:
            path = config_manager._path(scope)
            paths[scope] = {"path": str(path), "exists": path.exists()}
        except ValueError as exc:
            paths[scope] = {"error": str(exc)}
    return {
        "current": config_manager.registry.current(),
        "configs": paths,
        "recommendation": "Use discover_agents and install_mcp_server; bootstrap injects GOD_MCP_AGENT explicitly.",
    }


@mcp.tool()
def health_check() -> dict:
    """
    Check if godMCP server is running and healthy.

    Returns:
        dict: Health status information
    """
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "server": "godMCP",
        "version": "0.1.0",
        "message": "godMCP server is running",
    }


@mcp.tool()
def read_mcp_json(level: Optional[Literal["workspace", "user", "both"]] = "both") -> dict:
    """
    Read MCP configuration file(s).

    Returns the contents of workspace-level (.kiro/settings/mcp.json) and/or
    user-level (~/.kiro/settings/mcp.json) configuration files.

    Args:
        level: Which configuration to read - "workspace", "user", or "both" (default)

    Returns:
        dict: Configuration data with metadata about file locations and server counts
    """
    logger.info(f"Reading MCP configuration, level={level}")

    try:
        if level == "workspace":
            config = config_manager.read_workspace_config()
            result = {
                "level": "workspace",
                "config": config,
                "path": str(config_manager.get_workspace_config_path()),
                "serverCount": len(config.get("mcpServers", {})),
                "servers": list(config.get("mcpServers", {}).keys()),
            }
        elif level == "user":
            config = config_manager.read_user_config()
            result = {
                "level": "user",
                "config": config,
                "path": str(config_manager.get_user_config_path()),
                "serverCount": len(config.get("mcpServers", {})),
                "servers": list(config.get("mcpServers", {}).keys()),
            }
        else:  # both
            merged = config_manager.get_merged_config()
            workspace_config = config_manager.read_workspace_config()
            user_config = config_manager.read_user_config()

            result = {
                "level": "both",
                "merged": {
                    "config": {"mcpServers": merged.get("mcpServers", {})},
                    "serverCount": len(merged.get("mcpServers", {})),
                    "servers": list(merged.get("mcpServers", {}).keys()),
                },
                "workspace": {
                    "path": str(config_manager.get_workspace_config_path()),
                    "config": workspace_config,
                    "serverCount": len(workspace_config.get("mcpServers", {})),
                    "servers": list(workspace_config.get("mcpServers", {}).keys()),
                },
                "user": {
                    "path": str(config_manager.get_user_config_path()),
                    "config": user_config,
                    "serverCount": len(user_config.get("mcpServers", {})),
                    "servers": list(user_config.get("mcpServers", {}).keys()),
                },
                "metadata": merged.get("_metadata", {}),
            }

        logger.info(f"Successfully read MCP configuration, level={level}")
        return redact_config(result)

    except Exception as e:
        logger.error(f"Failed to read MCP configuration: {e}", exc_info=True)
        return {
            "error": str(e),
            "level": level,
            "message": f"Failed to read MCP configuration: {e}",
        }


def main():
    """Main entry point for the godMCP server."""
    logger.info("Starting godMCP server")
    mcp.run()


@mcp.tool()
def create_mcp_server(
    name: str,
    description: str,
    tools: list[dict],
    dependencies: Optional[list[str]] = None,
    output_dir: Optional[str] = None,
    register: bool = True,
    config_level: Literal["workspace", "user"] = "workspace",
    target_config_path: Optional[str] = None,
    targets: Optional[list[str]] = None,
) -> dict:
    """
    Create a new MCP server with custom tools and functionality.

    Generates a local Python package with pyproject.toml, server code,
    a portable descriptor, and documentation. Optionally registers the server in
    mcp.json configuration.

    Args:
        name: Server name (will be used for package name)
        description: Human-readable description of the server's purpose
        tools: List of tool specifications, each containing:
            - name: Tool name (must be valid Python identifier)
            - description: Tool description
            - parameters: JSON schema for tool parameters
            - return_type: Expected return type (default: "dict")
            - implementation: Python code to implement the tool (optional)
            - implementation_hint: Optional guidance for implementation (deprecated, use 'implementation')
        dependencies: Additional Python dependencies beyond FastMCP (optional)
        output_dir: Directory where the server package will be generated (optional)
        register: Whether to register the server in mcp.json (default: True)
        config_level: Configuration level for registration - "workspace" (default) or "user"
        target_config_path: Explicit JSON/TOML path (used when targets is absent)
        targets: Current, detected, all, or explicit agent IDs; takes precedence over path

    Returns:
        dict: Information about the created server package including paths and registration status
    """
    logger.info(f"Creating MCP server: name={name}, tools={len(tools)}")

    try:
        # Parse tool specifications
        tool_specs = []
        for i, tool_dict in enumerate(tools):
            try:
                # Accept both 'implementation_hint' and 'implementation' for backwards compatibility
                implementation = tool_dict.get("implementation") or tool_dict.get(
                    "implementation_hint"
                )

                tool_spec = ToolSpec(
                    name=tool_dict.get("name"),
                    description=tool_dict.get("description"),
                    parameters=tool_dict.get("parameters", {}),
                    return_type=tool_dict.get("return_type", "dict"),
                    implementation_hint=implementation,
                )
                tool_specs.append(tool_spec)
            except Exception as e:
                logger.error(f"Invalid tool specification at index {i}: {e}")
                return {
                    "success": False,
                    "error": "invalid_tool_spec",
                    "message": f"Invalid tool specification at index {i}: {e}",
                    "toolIndex": i,
                }

        # Create ServerSpec
        try:
            server_spec = ServerSpec(
                name=name,
                description=description,
                tools=tool_specs,
                dependencies=dependencies or [],
                output_dir=output_dir,
            )
        except ValueError as e:
            logger.error(f"Invalid server specification: {e}")
            return {
                "success": False,
                "error": "invalid_server_spec",
                "message": f"Invalid server specification: {e}",
            }

        # Create the server package
        result = server_creator.create_server(
            spec=server_spec,
            register=register,
            config_level=config_level,
            target_config_path=target_config_path,
            targets=targets,
        )

        if result.get("success"):
            logger.info(f"Successfully created MCP server: {name}")
        else:
            logger.error(f"Failed to create MCP server: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Failed to create MCP server: {e}", exc_info=True)
        return {
            "success": False,
            "error": "creation_failed",
            "message": f"Failed to create server: {e}",
            "serverName": name,
        }


@mcp.tool()
def update_mcp_json(
    server_name: str, server_config: dict, level: Literal["workspace", "user"] = "workspace"
) -> dict:
    """
    Add or update a server entry in the MCP configuration file.

    Validates the server configuration before writing and merges it into the
    appropriate mcp.json file without overwriting existing servers.

    Args:
        server_name: Name of the server to add/update
        server_config: Server configuration object with 'command', 'args', and optional fields
        level: Target configuration level - "workspace" (default) or "user"

    Returns:
        dict: Success confirmation with updated configuration details
    """
    logger.info(f"Updating MCP configuration: server={server_name}, level={level}")

    try:
        # Validate the server configuration
        config_manager.validate_server_config(server_config)

        # Add the server to the specified configuration
        config_manager.add_server(server_name, server_config, level)

        # Read back the updated configuration to confirm
        if level == "workspace":
            updated_config = config_manager.read_workspace_config()
            config_path = str(config_manager.get_workspace_config_path())
        else:
            updated_config = config_manager.read_user_config()
            config_path = str(config_manager.get_user_config_path())

        result = {
            "success": True,
            "message": f"Server '{server_name}' successfully added/updated in {level} configuration",
            "serverName": server_name,
            "level": level,
            "configPath": config_path,
            "serverConfig": redact_config(updated_config.get("mcpServers", {}).get(server_name)),
            "totalServers": len(updated_config.get("mcpServers", {})),
        }

        logger.info(f"Successfully updated MCP configuration: server={server_name}")
        return result

    except ValueError as e:
        logger.error(f"Validation error updating MCP configuration: {e}")
        return {
            "success": False,
            "error": "validation_error",
            "message": str(e),
            "serverName": server_name,
            "level": level,
        }
    except Exception as e:
        logger.error(f"Failed to update MCP configuration: {e}", exc_info=True)
        return {
            "success": False,
            "error": "update_failed",
            "message": f"Failed to update configuration: {e}",
            "serverName": server_name,
            "level": level,
        }


@mcp.tool()
def update_tool_implementation(server_name: str, tool_name: str, implementation: str) -> dict:
    """
    Update the implementation code of a specific tool in an MCP server.

    This tool allows you to modify the implementation of a tool after the server
    has been created. Useful for:
    - Fixing bugs in tool implementations
    - Adding functionality that was initially stubbed out
    - Updating tool behavior based on testing

    Args:
        server_name: Name of the MCP server containing the tool
        tool_name: Name of the tool to update
        implementation: New Python code for the tool implementation

    Returns:
        dict: Result of the update operation with file path and status
    """
    logger.info(f"Updating tool implementation: server={server_name}, tool={tool_name}")

    try:
        if not server_name or any(
            c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in server_name
        ):
            raise ValueError("Invalid server name")
        # Find the server directory
        server_dir = server_creator.base_output_dir / server_name
        if not server_dir.exists():
            return {
                "success": False,
                "error": "server_not_found",
                "message": f"Server directory not found: {server_dir}",
                "serverName": server_name,
            }

        # Find the server.py file
        package_name = server_name.replace("-", "_")
        server_file = server_dir / "src" / package_name / "server.py"

        if not server_file.exists():
            return {
                "success": False,
                "error": "server_file_not_found",
                "message": f"Server file not found: {server_file}",
                "serverName": server_name,
            }

        # Read the current server code
        server_code = server_file.read_text()

        # Locate the exact top-level function and validate before changing the file.
        import ast
        import textwrap

        tree = ast.parse(server_code)
        function = next(
            (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == tool_name), None
        )
        if function is None:
            raise ValueError("Tool function not found")
        lines = server_code.splitlines(keepends=True)
        body_start = function.body[0].lineno - 1
        if (
            isinstance(function.body[0], ast.Expr)
            and isinstance(function.body[0].value, ast.Constant)
            and isinstance(function.body[0].value.value, str)
        ):
            body_start = function.body[0].end_lineno
        replacement = textwrap.indent(textwrap.dedent(implementation).strip(), "    ") + "\n"
        new_server_code = (
            "".join(lines[:body_start]) + replacement + "".join(lines[function.end_lineno :])
        )
        ast.parse(new_server_code)
        server_file.write_text(new_server_code)

        logger.info(f"Successfully updated tool '{tool_name}' in server '{server_name}'")

        return {
            "success": True,
            "message": f"Tool '{tool_name}' implementation updated successfully",
            "serverName": server_name,
            "toolName": tool_name,
            "serverFile": str(server_file),
            "note": "Reconnect the MCP server for changes to take effect",
        }

    except Exception as e:
        logger.error(f"Failed to update tool implementation: {e}", exc_info=True)
        return {
            "success": False,
            "error": "update_failed",
            "message": f"Failed to update tool implementation: {e}",
            "serverName": server_name,
            "toolName": tool_name,
        }


@mcp.tool()
def remove_mcp_server(server_name: str, level: Literal["workspace", "user"] = "workspace") -> dict:
    """
    Remove a server entry from MCP configuration files.

    Removes the specified server only from the explicitly selected scope, if present.

    Args:
        server_name: Name of the server to remove

    Returns:
        dict: Confirmation of removal with details about where it was removed from
    """
    logger.info(f"Removing server from MCP configuration: server={server_name}")

    try:
        # Remove the server from both configurations
        removed_from = config_manager.remove_server(server_name, level)

        if not removed_from["workspace"] and not removed_from["user"]:
            result = {
                "success": False,
                "message": f"Server '{server_name}' not found in any configuration",
                "serverName": server_name,
                "removedFrom": removed_from,
            }
            logger.warning(f"Server '{server_name}' not found in any configuration")
        else:
            locations = []
            if removed_from["workspace"]:
                locations.append("workspace")
            if removed_from["user"]:
                locations.append("user")

            result = {
                "success": True,
                "message": f"Server '{server_name}' removed from {', '.join(locations)} configuration(s)",
                "serverName": server_name,
                "removedFrom": removed_from,
                "locations": locations,
            }
            logger.info(f"Successfully removed server '{server_name}' from {locations}")

        return result

    except Exception as e:
        logger.error(f"Failed to remove server from MCP configuration: {e}", exc_info=True)
        return {
            "success": False,
            "error": "removal_failed",
            "message": f"Failed to remove server: {e}",
            "serverName": server_name,
        }


@mcp.tool()
def discover_agents() -> dict:
    """List known agents, detection evidence, current harness and supported config scopes."""
    return {
        "current": config_manager.registry.current(),
        "agents": config_manager.registry.discover(),
    }


@mcp.tool()
def install_mcp_server(
    server_name: str,
    server_config: dict,
    targets: Optional[list[str]] = None,
    scope: Literal["workspace", "user"] = "workspace",
    dry_run: bool = True,
    replace: bool = False,
) -> dict:
    """Install a server into current, detected, all known, or named agents. Preview by default.

    Explicit names work even if an agent is not detected. all means all registered adapters.
    Set dry_run=False to apply an authorized installation. Configuration is not activation.
    Extend adapters with GOD_MCP_AGENTS_FILE. Pass credentials through the environment.
    """
    return config_manager.registry.install(
        server_name, server_config, targets, scope, dry_run, replace
    )


if __name__ == "__main__":
    main()

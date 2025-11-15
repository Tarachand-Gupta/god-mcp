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

# Configure logging for godMCP itself
log_file = Path.home() / ".kiro" / "god_mcp_debug.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("godMCP")

# Initialize FastMCP server
mcp = FastMCP("godMCP")

# Initialize ConfigManager and ServerCreator
config_manager = ConfigManager()
server_creator = ServerCreator(config_manager=config_manager)


@mcp.tool()
def get_config_info() -> dict:
    """
    Get information about current MCP configuration paths being used.
    
    Shows which configuration files are being used for workspace and user levels,
    whether they exist, and their source (environment variable or fallback).
    
    Returns:
        dict: Configuration information including paths, existence, and sources
    """
    logger.info("Getting configuration info")
    
    workspace_path = config_manager.get_workspace_config_path()
    user_path = config_manager.get_user_config_path()
    
    workspace_env = os.getenv("WORKSPACE_MCP_CONFIG_PATH")
    user_env = os.getenv("USER_MCP_CONFIG_PATH")
    
    return {
        "workspace_config": {
            "path": str(workspace_path),
            "source": "environment_variable" if workspace_env else "fallback",
            "env_var": "WORKSPACE_MCP_CONFIG_PATH",
            "env_value": workspace_env,
            "exists": workspace_path.exists(),
            "writable": os.access(workspace_path.parent, os.W_OK) if workspace_path.parent.exists() else False
        },
        "user_config": {
            "path": str(user_path),
            "source": "environment_variable" if user_env else "fallback",
            "env_var": "USER_MCP_CONFIG_PATH",
            "env_value": user_env,
            "exists": user_path.exists(),
            "writable": os.access(user_path.parent, os.W_OK) if user_path.parent.exists() else False
        },
        "recommendation": "Set WORKSPACE_MCP_CONFIG_PATH and USER_MCP_CONFIG_PATH environment variables in your godMCP server configuration for explicit control."
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
        "message": "godMCP server is running"
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
                "servers": list(config.get("mcpServers", {}).keys())
            }
        elif level == "user":
            config = config_manager.read_user_config()
            result = {
                "level": "user",
                "config": config,
                "path": str(config_manager.get_user_config_path()),
                "serverCount": len(config.get("mcpServers", {})),
                "servers": list(config.get("mcpServers", {}).keys())
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
                    "servers": list(merged.get("mcpServers", {}).keys())
                },
                "workspace": {
                    "path": str(config_manager.get_workspace_config_path()),
                    "config": workspace_config,
                    "serverCount": len(workspace_config.get("mcpServers", {})),
                    "servers": list(workspace_config.get("mcpServers", {}).keys())
                },
                "user": {
                    "path": str(config_manager.get_user_config_path()),
                    "config": user_config,
                    "serverCount": len(user_config.get("mcpServers", {})),
                    "servers": list(user_config.get("mcpServers", {}).keys())
                },
                "metadata": merged.get("_metadata", {})
            }
        
        logger.info(f"Successfully read MCP configuration, level={level}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to read MCP configuration: {e}", exc_info=True)
        return {
            "error": str(e),
            "level": level,
            "message": f"Failed to read MCP configuration: {e}"
        }


def main():
    """Main entry point for the godMCP server."""
    logger.info("Starting godMCP server")
    mcp.run()


if __name__ == "__main__":
    main()



@mcp.tool()
def create_mcp_server(
    name: str,
    description: str,
    tools: list[dict],
    dependencies: Optional[list[str]] = None,
    output_dir: Optional[str] = None,
    register: bool = True,
    config_level: Literal["workspace", "user"] = "workspace",
    target_config_path: Optional[str] = None
) -> dict:
    """
    Create a new MCP server with custom tools and functionality.
    
    Generates a complete Python package structure with pyproject.toml, server code,
    logging infrastructure, and documentation. Optionally registers the server in
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
        target_config_path: Explicit path to mcp.json file (overrides config_level and env vars)
    
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
                implementation = tool_dict.get("implementation") or tool_dict.get("implementation_hint")
                
                tool_spec = ToolSpec(
                    name=tool_dict.get("name"),
                    description=tool_dict.get("description"),
                    parameters=tool_dict.get("parameters", {}),
                    return_type=tool_dict.get("return_type", "dict"),
                    implementation_hint=implementation
                )
                tool_specs.append(tool_spec)
            except Exception as e:
                logger.error(f"Invalid tool specification at index {i}: {e}")
                return {
                    "success": False,
                    "error": "invalid_tool_spec",
                    "message": f"Invalid tool specification at index {i}: {e}",
                    "toolIndex": i
                }
        
        # Create ServerSpec
        try:
            server_spec = ServerSpec(
                name=name,
                description=description,
                tools=tool_specs,
                dependencies=dependencies or [],
                output_dir=output_dir
            )
        except ValueError as e:
            logger.error(f"Invalid server specification: {e}")
            return {
                "success": False,
                "error": "invalid_server_spec",
                "message": f"Invalid server specification: {e}"
            }
        
        # Update output directory if specified
        if output_dir:
            from pathlib import Path
            server_creator.base_output_dir = Path(output_dir)
        
        # Create the server package
        result = server_creator.create_server(
            spec=server_spec,
            register=register,
            config_level=config_level,
            target_config_path=target_config_path
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
            "serverName": name
        }


@mcp.tool()
def update_mcp_json(
    server_name: str,
    server_config: dict,
    level: Literal["workspace", "user"] = "workspace"
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
            "serverConfig": updated_config.get("mcpServers", {}).get(server_name),
            "totalServers": len(updated_config.get("mcpServers", {}))
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
            "level": level
        }
    except Exception as e:
        logger.error(f"Failed to update MCP configuration: {e}", exc_info=True)
        return {
            "success": False,
            "error": "update_failed",
            "message": f"Failed to update configuration: {e}",
            "serverName": server_name,
            "level": level
        }



@mcp.tool()
def update_tool_implementation(
    server_name: str,
    tool_name: str,
    implementation: str
) -> dict:
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
        # Find the server directory
        server_dir = server_creator.base_output_dir / server_name
        if not server_dir.exists():
            return {
                "success": False,
                "error": "server_not_found",
                "message": f"Server directory not found: {server_dir}",
                "serverName": server_name
            }
        
        # Find the server.py file
        package_name = server_name.replace('-', '_')
        server_file = server_dir / "src" / package_name / "server.py"
        
        if not server_file.exists():
            return {
                "success": False,
                "error": "server_file_not_found",
                "message": f"Server file not found: {server_file}",
                "serverName": server_name
            }
        
        # Read the current server code
        server_code = server_file.read_text()
        
        # Find the tool function
        import re
        
        # Pattern to match the tool function including decorator and full body
        pattern = rf'(@mcp\.tool\(\)\s+@logged_tool\s+def {tool_name}\([^)]*\)[^:]*:.*?)(?=\n@mcp\.tool\(\)|\ndef main\(\):|\Z)'
        
        match = re.search(pattern, server_code, re.DOTALL)
        
        if not match:
            return {
                "success": False,
                "error": "tool_not_found",
                "message": f"Tool '{tool_name}' not found in server '{server_name}'",
                "serverName": server_name,
                "toolName": tool_name,
                "serverFile": str(server_file)
            }
        
        old_function = match.group(1)
        
        # Extract the function signature (everything up to the docstring or first line of code)
        sig_match = re.search(r'(@mcp\.tool\(\)\s+@logged_tool\s+def ' + tool_name + r'\([^)]*\)[^:]*:)\s+(""".*?"""|\'\'\'.*?\'\'\')?', old_function, re.DOTALL)
        
        if not sig_match:
            return {
                "success": False,
                "error": "parse_error",
                "message": f"Could not parse function signature for tool '{tool_name}'",
                "serverName": server_name,
                "toolName": tool_name
            }
        
        function_signature = sig_match.group(1)
        docstring = sig_match.group(2) if sig_match.group(2) else ""
        
        # Ensure implementation is properly indented
        implementation_lines = implementation.strip().split('\n')
        indented_implementation = '\n    '.join([''] + implementation_lines)
        
        # Build the new function
        new_function = f"{function_signature}\n{docstring}{indented_implementation}\n"
        
        # Replace the old function with the new one
        new_server_code = server_code.replace(old_function, new_function)
        
        # Write the updated code back
        server_file.write_text(new_server_code)
        
        logger.info(f"Successfully updated tool '{tool_name}' in server '{server_name}'")
        
        return {
            "success": True,
            "message": f"Tool '{tool_name}' implementation updated successfully",
            "serverName": server_name,
            "toolName": tool_name,
            "serverFile": str(server_file),
            "note": "Reconnect the MCP server for changes to take effect"
        }
        
    except Exception as e:
        logger.error(f"Failed to update tool implementation: {e}", exc_info=True)
        return {
            "success": False,
            "error": "update_failed",
            "message": f"Failed to update tool implementation: {e}",
            "serverName": server_name,
            "toolName": tool_name
        }


@mcp.tool()
def remove_mcp_server(server_name: str) -> dict:
    """
    Remove a server entry from MCP configuration files.
    
    Removes the specified server from both workspace and user-level mcp.json files
    if present.
    
    Args:
        server_name: Name of the server to remove
    
    Returns:
        dict: Confirmation of removal with details about where it was removed from
    """
    logger.info(f"Removing server from MCP configuration: server={server_name}")
    
    try:
        # Remove the server from both configurations
        removed_from = config_manager.remove_server(server_name)
        
        if not removed_from["workspace"] and not removed_from["user"]:
            result = {
                "success": False,
                "message": f"Server '{server_name}' not found in any configuration",
                "serverName": server_name,
                "removedFrom": removed_from
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
                "locations": locations
            }
            logger.info(f"Successfully removed server '{server_name}' from {locations}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to remove server from MCP configuration: {e}", exc_info=True)
        return {
            "success": False,
            "error": "removal_failed",
            "message": f"Failed to remove server: {e}",
            "serverName": server_name
        }

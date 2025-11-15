"""
Configuration manager for MCP configuration files.
Handles reading, writing, and merging workspace and user-level mcp.json files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("godMCP.ConfigManager")


class ConfigManager:
    """
    Manages MCP configuration files at workspace and user levels.
    
    Handles path resolution, reading, merging, and updating mcp.json files
    with proper precedence (workspace overrides user).
    """
    
    def __init__(self, workspace_dir: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Reads configuration paths from environment variables:
        - WORKSPACE_MCP_CONFIG_PATH: Path to workspace-level mcp.json
        - USER_MCP_CONFIG_PATH: Path to user-level mcp.json
        
        Args:
            workspace_dir: Optional workspace directory path (deprecated, kept for compatibility)
        """
        # Read paths from environment variables
        workspace_env = os.getenv("WORKSPACE_MCP_CONFIG_PATH")
        user_env = os.getenv("USER_MCP_CONFIG_PATH")
        
        if workspace_env:
            self.workspace_config_path = Path(workspace_env)
            logger.info(f"Using WORKSPACE_MCP_CONFIG_PATH from env: {self.workspace_config_path}")
        else:
            # Fallback to old behavior for backward compatibility
            self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
            self.workspace_config_path = self.workspace_dir / ".kiro" / "settings" / "mcp.json"
            logger.warning(f"WORKSPACE_MCP_CONFIG_PATH not set, using fallback: {self.workspace_config_path}")
        
        if user_env:
            self.user_config_path = Path(user_env)
            logger.info(f"Using USER_MCP_CONFIG_PATH from env: {self.user_config_path}")
        else:
            # Fallback to default user config
            self.user_config_path = Path.home() / ".kiro" / "settings" / "mcp.json"
            logger.warning(f"USER_MCP_CONFIG_PATH not set, using fallback: {self.user_config_path}")
        
        logger.info(f"ConfigManager initialized")
        logger.info(f"Workspace config: {self.workspace_config_path}")
        logger.info(f"User config: {self.user_config_path}")
    
    def _resolve_path(self, path: Path) -> Path:
        """
        Resolve path with home directory expansion.
        
        Args:
            path: Path to resolve
        
        Returns:
            Resolved absolute path
        """
        return path.expanduser().resolve()
    
    def get_workspace_config_path(self) -> Path:
        """
        Get the workspace-level mcp.json path.
        
        Returns:
            Path to workspace mcp.json
        """
        return self._resolve_path(self.workspace_config_path)
    
    def get_user_config_path(self) -> Path:
        """
        Get the user-level mcp.json path.
        
        Returns:
            Path to user mcp.json
        """
        return self._resolve_path(self.user_config_path)

    def read_workspace_config(self) -> dict:
        """
        Read workspace-level mcp.json configuration.
        
        Returns:
            Configuration dictionary. Returns empty structure if file doesn't exist.
        """
        config_path = self.get_workspace_config_path()
        
        if not config_path.exists():
            logger.info(f"Workspace config not found at {config_path}")
            return {"mcpServers": {}}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Loaded workspace config with {len(config.get('mcpServers', {}))} servers")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse workspace config: {e}")
            raise ValueError(f"Invalid JSON in workspace config: {e}")
        except Exception as e:
            logger.error(f"Failed to read workspace config: {e}")
            raise
    
    def read_user_config(self) -> dict:
        """
        Read user-level mcp.json configuration.
        
        Returns:
            Configuration dictionary. Returns empty structure if file doesn't exist.
        """
        config_path = self.get_user_config_path()
        
        if not config_path.exists():
            logger.info(f"User config not found at {config_path}")
            return {"mcpServers": {}}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Loaded user config with {len(config.get('mcpServers', {}))} servers")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse user config: {e}")
            raise ValueError(f"Invalid JSON in user config: {e}")
        except Exception as e:
            logger.error(f"Failed to read user config: {e}")
            raise
    
    def get_merged_config(self) -> dict:
        """
        Get merged configuration with workspace taking precedence over user.
        
        Returns:
            Merged configuration dictionary with metadata about sources
        """
        user_config = self.read_user_config()
        workspace_config = self.read_workspace_config()
        
        # Start with user config servers
        merged_servers = user_config.get("mcpServers", {}).copy()
        
        # Overlay workspace config (workspace takes precedence)
        workspace_servers = workspace_config.get("mcpServers", {})
        merged_servers.update(workspace_servers)
        
        logger.info(f"Merged config contains {len(merged_servers)} total servers")
        
        return {
            "mcpServers": merged_servers,
            "_metadata": {
                "userConfigPath": str(self.get_user_config_path()),
                "workspaceConfigPath": str(self.get_workspace_config_path()),
                "userServerCount": len(user_config.get("mcpServers", {})),
                "workspaceServerCount": len(workspace_servers),
                "totalServerCount": len(merged_servers)
            }
        }

    def validate_server_config(self, config: dict) -> bool:
        """
        Validate server configuration against expected schema.
        
        Args:
            config: Server configuration dictionary
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ["command", "args"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate command is a string
        if not isinstance(config["command"], str):
            raise ValueError("'command' must be a string")
        
        # Validate args is a list
        if not isinstance(config["args"], list):
            raise ValueError("'args' must be a list")
        
        # Validate optional fields if present
        if "env" in config and not isinstance(config["env"], dict):
            raise ValueError("'env' must be a dictionary")
        
        if "disabled" in config and not isinstance(config["disabled"], bool):
            raise ValueError("'disabled' must be a boolean")
        
        if "autoApprove" in config and not isinstance(config["autoApprove"], list):
            raise ValueError("'autoApprove' must be a list")
        
        logger.info("Server configuration validated successfully")
        return True
    
    def add_server(self, name: str, config: dict, level: str = "workspace") -> None:
        """
        Add or update a server entry in the specified configuration file.
        
        Args:
            name: Server name
            config: Server configuration dictionary
            level: Configuration level ('workspace' or 'user')
        
        Raises:
            ValueError: If configuration is invalid or level is unknown
        """
        # Validate configuration
        self.validate_server_config(config)
        
        # Determine target file
        if level == "workspace":
            config_path = self.get_workspace_config_path()
        elif level == "user":
            config_path = self.get_user_config_path()
        else:
            raise ValueError(f"Invalid level: {level}. Must be 'workspace' or 'user'")
        
        # Read existing config or create new structure
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = json.load(f)
        else:
            full_config = {"mcpServers": {}}
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add or update server
        if "mcpServers" not in full_config:
            full_config["mcpServers"] = {}
        
        full_config["mcpServers"][name] = config
        
        # Write atomically using temp file
        temp_path = config_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2)
            
            # Atomic rename
            temp_path.replace(config_path)
            logger.info(f"Added server '{name}' to {level} config at {config_path}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"Failed to write config: {e}")
            raise
    
    def remove_server(self, name: str) -> dict:
        """
        Remove a server entry from both workspace and user configuration files.
        
        Args:
            name: Server name to remove
        
        Returns:
            Dictionary indicating where the server was removed from
        """
        removed_from = {"workspace": False, "user": False}
        
        # Try removing from workspace config
        workspace_path = self.get_workspace_config_path()
        if workspace_path.exists():
            try:
                with open(workspace_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if name in config.get("mcpServers", {}):
                    del config["mcpServers"][name]
                    
                    # Write atomically
                    temp_path = workspace_path.with_suffix('.json.tmp')
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    temp_path.replace(workspace_path)
                    
                    removed_from["workspace"] = True
                    logger.info(f"Removed server '{name}' from workspace config")
            except Exception as e:
                logger.error(f"Failed to remove from workspace config: {e}")
        
        # Try removing from user config
        user_path = self.get_user_config_path()
        if user_path.exists():
            try:
                with open(user_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if name in config.get("mcpServers", {}):
                    del config["mcpServers"][name]
                    
                    # Write atomically
                    temp_path = user_path.with_suffix('.json.tmp')
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    temp_path.replace(user_path)
                    
                    removed_from["user"] = True
                    logger.info(f"Removed server '{name}' from user config")
            except Exception as e:
                logger.error(f"Failed to remove from user config: {e}")
        
        if not removed_from["workspace"] and not removed_from["user"]:
            logger.warning(f"Server '{name}' not found in any config")
        
        return removed_from

"""
Data models for godMCP server and tool specifications.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolSpec:
    """
    Specification for a tool to be generated in an MCP server.
    
    Attributes:
        name: Tool name (must be valid Python identifier)
        description: Human-readable description of what the tool does
        parameters: JSON schema for tool parameters
        return_type: Expected return type (e.g., "dict", "str", "list")
        implementation_hint: Optional guidance for implementation
    """
    name: str
    description: str
    parameters: dict
    return_type: str = "dict"
    implementation_hint: Optional[str] = None
    
    def __post_init__(self):
        """Validate tool specification."""
        if not self.name:
            raise ValueError("Tool name is required")
        
        if not self.name.isidentifier():
            raise ValueError(f"Tool name '{self.name}' must be a valid Python identifier")
        
        if not self.description:
            raise ValueError("Tool description is required")
        
        if not isinstance(self.parameters, dict):
            raise ValueError("Tool parameters must be a dictionary (JSON schema)")
        
        if not self.return_type:
            raise ValueError("Tool return_type is required")


@dataclass
class ServerSpec:
    """
    Specification for an MCP server to be generated.
    
    Attributes:
        name: Server name (will be used for package name)
        description: Human-readable description of the server's purpose
        tools: List of tool specifications
        dependencies: Additional Python dependencies beyond FastMCP
        output_dir: Directory where the server package will be generated
    """
    name: str
    description: str
    tools: list[ToolSpec]
    dependencies: list[str] = field(default_factory=list)
    output_dir: Optional[str] = None
    
    def __post_init__(self):
        """Validate server specification."""
        if not self.name:
            raise ValueError("Server name is required")
        
        # Validate name is suitable for package name (lowercase, hyphens allowed)
        if not all(c.isalnum() or c in '-_' for c in self.name):
            raise ValueError(
                f"Server name '{self.name}' must contain only alphanumeric characters, hyphens, and underscores"
            )
        
        if not self.description:
            raise ValueError("Server description is required")
        
        if not self.tools:
            raise ValueError("At least one tool is required")
        
        if not isinstance(self.tools, list):
            raise ValueError("Tools must be a list of ToolSpec objects")
        
        # Validate all tools are ToolSpec instances
        for i, tool in enumerate(self.tools):
            if not isinstance(tool, ToolSpec):
                raise ValueError(f"Tool at index {i} must be a ToolSpec instance")
        
        # Check for duplicate tool names
        tool_names = [tool.name for tool in self.tools]
        if len(tool_names) != len(set(tool_names)):
            duplicates = [name for name in tool_names if tool_names.count(name) > 1]
            raise ValueError(f"Duplicate tool names found: {set(duplicates)}")
    
    def get_package_name(self) -> str:
        """
        Get the Python package name (snake_case version of server name).
        
        Returns:
            Package name suitable for Python imports
        """
        return self.name.replace('-', '_')
    
    def get_all_dependencies(self) -> list[str]:
        """
        Get all dependencies including FastMCP and custom ones.
        
        Returns:
            List of all required dependencies
        """
        base_deps = ["fastmcp>=0.1.0"]
        return base_deps + self.dependencies

"""
Templates for generating MCP server packages.
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


def get_template(template_name: str) -> str:
    """
    Load a template file.
    
    Args:
        template_name: Name of the template file
    
    Returns:
        Template content as string
    """
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    return template_path.read_text()

# Contributing to godMCP

Thank you for your interest in contributing to godMCP! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Installation

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/godmcp.git
   cd godmcp/god-mcp
   ```

3. Install dependencies using uv:
   ```bash
   uv sync
   ```

4. Verify the installation:
   ```bash
   uv run god-mcp --help
   ```

## Development Setup

### Setting up your development environment

1. Create a virtual environment (uv handles this automatically):
   ```bash
   uv venv
   ```

2. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

3. Configure your MCP client to use the local development version:
   ```json
   {
     "mcpServers": {
       "godMCP-dev": {
         "command": "uv",
         "args": [
           "run",
           "--directory",
           "/path/to/your/godmcp/god-mcp",
           "god-mcp"
         ],
         "env": {
           "FASTMCP_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

## Project Structure

```
god-mcp/
├── src/
│   └── god_mcp/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # Main FastMCP server with tools
│       ├── config_manager.py    # MCP configuration management
│       ├── server_creator.py    # Server package generation
│       ├── models.py            # Data models (ServerSpec, ToolSpec)
│       └── templates/           # Code generation templates
├── pyproject.toml               # Project configuration
├── README.md                    # Project documentation
├── CONTRIBUTING.md              # This file
└── .gitignore                   # Git ignore rules
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, concise code
- Follow the existing code style
- Add docstrings to all functions and classes
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run the server locally
uv run god-mcp

# Test specific functionality
python -c "from god_mcp import server; print(server.mcp.get_tools())"
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commit messages:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## Testing

### Manual Testing

1. **Test Server Creation:**
   ```python
   from god_mcp.server_creator import ServerCreator
   from god_mcp.models import ServerSpec, ToolSpec
   
   tool = ToolSpec(
       name="test_tool",
       description="A test tool",
       parameters={"type": "object", "properties": {}},
       return_type="dict"
   )
   
   spec = ServerSpec(
       name="test-server",
       description="Test server",
       tools=[tool]
   )
   
   creator = ServerCreator()
   result = creator.create_server(spec, register=False)
   print(result)
   ```

2. **Test Configuration Management:**
   ```python
   from god_mcp.config_manager import ConfigManager
   
   manager = ConfigManager()
   config = manager.read_workspace_config()
   print(config)
   ```

3. **Test MCP Tools:**
   - Use your MCP client (Kiro, Claude Desktop, etc.)
   - Test each tool with various inputs
   - Verify error handling

### Writing Tests

When adding new features, consider adding test scripts:

```python
#!/usr/bin/env python3
"""Test script for new feature."""

import sys
from pathlib import Path

# Add god-mcp to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from god_mcp import server

def test_new_feature():
    """Test the new feature."""
    # Your test code here
    pass

if __name__ == "__main__":
    test_new_feature()
```

## Code Style

### Python Style Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable names

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> dict:
    """
    Brief description of the function.
    
    Longer description if needed, explaining the purpose
    and behavior of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

### Code Organization

- Keep functions focused and single-purpose
- Use classes for related functionality
- Separate concerns (e.g., config management, server creation)
- Add logging for important operations

## Submitting Changes

### Pull Request Process

1. **Update Documentation:**
   - Update README.md if adding new features
   - Add docstrings to new functions/classes
   - Update examples if behavior changes

2. **Create Pull Request:**
   - Push your branch to your fork
   - Create a PR against the main repository
   - Fill out the PR template with:
     - Description of changes
     - Related issues
     - Testing performed
     - Screenshots (if applicable)

3. **PR Review:**
   - Address reviewer feedback
   - Keep the PR focused on a single feature/fix
   - Ensure all discussions are resolved

4. **Merge:**
   - Maintainers will merge once approved
   - Delete your feature branch after merge

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Manual testing performed
- [ ] Commit messages follow conventional format
- [ ] No unnecessary files included
- [ ] Changes are focused and atomic

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Description:** Clear description of the bug
2. **Steps to Reproduce:**
   ```
   1. Step one
   2. Step two
   3. Expected vs actual behavior
   ```
3. **Environment:**
   - OS and version
   - Python version
   - godMCP version
   - MCP client used

4. **Logs:** Include relevant logs from `~/.kiro/god_mcp_debug.log`

5. **Screenshots:** If applicable

### Feature Requests

When requesting features, include:

1. **Use Case:** Describe the problem you're trying to solve
2. **Proposed Solution:** Your idea for how to solve it
3. **Alternatives:** Other solutions you've considered
4. **Additional Context:** Any other relevant information

## Development Tips

### Debugging

1. **Enable Debug Logging:**
   ```json
   {
     "env": {
       "FASTMCP_LOG_LEVEL": "DEBUG"
     }
   }
   ```

2. **Check Logs:**
   ```bash
   tail -f ~/.kiro/god_mcp_debug.log
   ```

3. **Use Python Debugger:**
   ```python
   import pdb; pdb.set_trace()
   ```

### Common Tasks

**Add a New Tool:**

1. Add tool function in `src/god_mcp/server.py`:
   ```python
   @mcp.tool()
   def new_tool(param: str) -> dict:
       """Tool description."""
       logger.info(f"New tool called with: {param}")
       # Implementation
       return {"result": "success"}
   ```

2. Test the tool
3. Update documentation

**Modify Server Generation:**

1. Edit `src/god_mcp/server_creator.py`
2. Update template generation methods
3. Test with various server configurations

**Update Configuration Management:**

1. Edit `src/god_mcp/config_manager.py`
2. Ensure backward compatibility
3. Test with existing configurations

## Questions?

If you have questions:

1. Check existing issues and discussions
2. Review the documentation
3. Open a new issue with the "question" label

## License

By contributing to godMCP, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to godMCP! 🚀

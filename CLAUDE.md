# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python FastMCP server that exposes GritQL capabilities for code searching and rewriting to MCP-compatible clients. The server acts as a wrapper around the `grit` CLI tool, parsing its human-readable output since structured JSON output is not yet available.

### Container Use Integration

The server supports two execution modes for mutating operations (apply/dry_run):
1. **Host Mode** (default): Executes commands directly on the host filesystem
2. **Container Mode**: Executes commands inside Container Use environments via Docker

This integration allows gritql-mcp to work safely with Container Use, where:
- gritql-mcp handles discovery and executes transformations inside containers
- Container Use manages container lifecycle and handles landing changes
- The agent orchestrates both servers to safely apply code transformations

## Development Commands

### Setup and Dependencies
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install in editable mode
uv pip install -e .

# Install with dev dependencies (for testing and linting)
uv pip install -e .[dev]
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_handlers.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Check linting errors
ruff check .

# Auto-fix linting errors
ruff check --fix .

# Check code formatting
ruff format --check .

# Auto-format code
ruff format .
```

### Running the Server
```bash
# Run directly
python -m server.main

# Or using the script
./scripts/run-stdio.sh
```

## Architecture

### Core Components

1. **MCP Instance** (`server/mcp_instance.py`): FastMCP server singleton that handles tool registration
2. **Main Entry** (`server/main.py`): Imports handlers to register tools via decorators and runs the MCP server
3. **Handlers** (`server/handlers/`): Tool implementations that wrap `grit` CLI commands
   - `find.py`: Find code matches using `grit check`
   - `apply.py`: Apply rewrites using `grit apply`
   - `dry_run.py`: Preview changes with `grit apply --dry-run`
   - `generate.py`: Generate GritQL from natural language
   - `library.py`: Search and describe available patterns
4. **Parsing** (`server/parsing/`): Parse human-readable `grit` CLI output
5. **Policy** (`server/policy/`): Security gating for language and command restrictions

### Tool Interface

All tools follow a pattern of:
1. Validating input parameters
2. Applying security policies via `gating` module
3. Building `grit` CLI command with proper escaping
4. Running subprocess with `--` separator for path arguments
5. Parsing and returning output or errors

### Environment Variables

- `GRIT_CLI_PATH`: Override default `grit` executable location

## Testing Approach

The test suite uses:
- `pytest` with `pytest-asyncio` for async tests
- Full MCP host simulation using FastMCP client
- Mock subprocess calls for unit testing handlers
- Hardcoded test path: `/home/johann/.nvm/versions/node/v23.9.0/bin/grit`

## Key Patterns

1. **Command Safety**: Always use `--` before path arguments to prevent parameter injection
2. **Error Handling**: Return `{"error": message}` for failures, `{"output": text}` for success
3. **Tool Registration**: Use `@mcp.tool()` decorator in handler modules
4. **CLI Parsing**: Parse human-readable output since JSON format unavailable
5. **Execution Modes**: Check `execution_target` parameter to determine host vs container mode

### Container Mode Usage

When tools receive `execution_target` with `type: "container_use"`:
1. Execute grit commands inside the specified container via Docker
2. Return actual execution results (stdout/stderr)
3. Include risk assessment metadata for agent decision-making
4. Provide troubleshooting information if execution fails

Example execution_target:
```python
{
    "type": "container_use",
    "env_id": "container_env_123",  # Container Use environment ID
    "cwd": "/workspace/project"      # Working directory inside container
}
```

The server uses the Docker Python SDK (docker-py) to execute commands in containers named `container-use-env-{env_id}`. This provides better error handling, container status validation, and more robust execution compared to subprocess calls.
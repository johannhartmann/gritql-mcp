# GritQL MCP Server

This project implements a local-only Python [FastMCP](https://gofastmcp.com/) server that exposes the capabilities of the [GritQL engine](https://docs.grit.io/) to MCP-compatible clients like the Gemini CLI.

The server allows you to leverage GritQL for code searching and rewriting directly from your development environment. All operations are performed locally by shelling out to the `grit` command-line tool.

## Features

The server exposes the following tools to the client, acting as a wrapper around the `grit` CLI:

-   `library.search_patterns`: Lists available patterns by parsing the output of `grit patterns list` and `grit list`.
-   `patterns.describe`: Shows metadata for a pattern by parsing the output of `grit patterns describe`.
-   `gritql.generate`: Deterministically generates a GritQL query from a natural language problem description (local-only, no AI).
-   `code.find`: Finds code matches using `grit check`. Returns the raw text output from the CLI.
-   `code.dry_run`: Shows a diff of potential changes using `grit apply --dry-run`. Returns the raw text output.
-   `code.apply`: Applies a rewrite to your codebase using `grit apply`. Returns the raw text output.

**Note:** This server parses the human-readable output of the `grit` CLI, as the tool does not yet support structured (JSON) output for these commands.

### Container Use Integration

The `code.apply` and `code.dry_run` tools support an optional `execution_target` parameter for integration with [Container Use](https://container-use.com):

-   **Host Mode** (default): Executes commands directly on the host filesystem
-   **Container Mode**: Returns command specifications for isolated execution via Container Use MCP

When using Container Mode, the tools return:
-   Exact shell commands to run in the container
-   Risk assessment metadata (scope, impact level, affected languages)
-   Instructions for reviewing and landing changes

This allows agents to safely test and apply code transformations in isolated environments before committing changes.

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python** (3.8 or higher)
2.  **uv**: Follow the official installation instructions at [astral.sh/uv](https://astral.sh/uv).
3.  **Grit CLI**: You can install the Grit CLI using either `npm` or a `curl` script. For more details, see the [official quickstart guide](https://docs.grit.io/cli/quickstart).

    *   **npm**

        ```bash
        npm install --location=global @getgrit/cli
        ```

    *   **curl**

        ```bash
        curl -fsSL https://docs.grit.io/install | bash
        ```
4.  **An MCP-compatible client** (e.g., Gemini CLI).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd gritql-mcp
    ```

2.  **Install Python dependencies**:
    ```bash
    # Create and activate a virtual environment
    uv venv
    source .venv/bin/activate

    # Install the package in editable mode
    uv pip install -e .
    ```

## Configuration

To make the server available to the Gemini CLI, you need to add it to your configuration file.

1.  Locate or create the config file at `~/.gemini/settings.json`.

2.  Add the following to the `mcp_servers` list in the file:

    ```json
    {
      "command": "python",
      "args": ["-m", "server.main"],
      "name": "gritql"
    }
    ```

3.  **(Optional) If `grit` is not in your PATH:**
    If the `grit` executable is not in a standard location, you can tell the server where to find it by adding a `GRIT_CLI_PATH` environment variable to your configuration:
    ```json
    {
      "command": "python",
      "args": ["-m", "server.main"],
      "name": "gritql",
      "env": {
        "GRIT_CLI_PATH": "/path/to/your/grit-executable"
      }
    }
    ```

## Usage

Once configured, your MCP client will automatically start and connect to the server. You can then invoke the tools by describing what you want to do.

**Example (with Gemini CLI):**

1.  Navigate to your workspace.
2.  Run the Gemini CLI: `gemini`
3.  Give it a prompt that triggers one of the tools:
    > "Using the gritql tool, find all functions named 'my_function'."

The CLI will identify the appropriate tool (`code.find`), call the server, and display the results.

## Container Use Integration Guide

This section explains how to use gritql-mcp with Container Use for safe, isolated code transformations.

### Architecture Overview

The integration follows a responsibility split model:

- **gritql-mcp** (on host): Handles pattern discovery, planning, risk assessment, and command generation
- **Container Use** (isolated environment): Creates containers, executes commands, generates diffs, and lands changes
- **Agent** (orchestrator): Coordinates both servers to safely apply transformations

### Installation Requirements

#### Host Environment

Install on your host machine where the agent runs:

1. **gritql-mcp server:**
   ```bash
   git clone <repository-url>
   cd gritql-mcp
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

2. **Container Use MCP:**
   Follow the [Container Use quickstart](https://container-use.com/quickstart) to install.

3. **Configure both MCP servers** in your agent's configuration (e.g., `~/.gemini/settings.json`):
   ```json
   {
     "mcp_servers": [
       {
         "command": "python",
         "args": ["-m", "server.main"],
         "name": "gritql",
         "cwd": "/path/to/gritql-mcp"
       },
       {
         "command": "container-use",
         "args": ["stdio"],
         "name": "container-use"
       }
     ]
   }
   ```

#### Container Environment

The Grit CLI must be available inside the container for execution:

1. **Option A - Pre-installed in container image:**
   ```dockerfile
   # In your Dockerfile
   RUN npm install -g @getgrit/cli
   # OR
   RUN curl -fsSL https://docs.grit.io/install | bash
   ```

2. **Option B - Install during container initialization:**
   Use Container Use's `environment_run_cmd` to install Grit when creating the environment:
   ```python
   # Agent code
   await client.call_tool("environment_run_cmd", {
       "env_id": env_id,
       "command": "npm install -g @getgrit/cli"
   })
   ```

### Agent Workflow

Here's how an agent orchestrates both servers for safe code transformations:

#### 1. Discovery Phase (Host)

Use gritql-mcp to explore available patterns and understand the codebase:

```python
# Find available patterns
patterns = await client.call_tool("library.search_patterns", {
    "query": "react",
    "language": "javascript"
})

# Check what a pattern does
description = await client.call_tool("patterns.describe", {
    "name": "react_to_hooks"
})

# Find matching code without changes
matches = await client.call_tool("code.find", {
    "patternName": "react_to_hooks",
    "paths": ["src/"]
})
```

#### 2. Environment Setup (Container Use)

Create an isolated container environment:

```python
# Create container environment
env = await client.call_tool("environment_create", {
    "base_image": "node:20",
    "working_dir": "/workspace"
})
env_id = env["env_id"]

# Clone or copy code into container
await client.call_tool("environment_run_cmd", {
    "env_id": env_id,
    "command": "git clone https://github.com/user/repo.git ."
})
```

#### 3. Planning Phase (Host → Container)

Get transformation plan from gritql-mcp in container mode:

```python
# Get dry run plan with risk assessment
plan = await client.call_tool("code.dry_run", {
    "patternName": "react_to_hooks",
    "paths": ["src/components"],
    "execution_target": {
        "type": "container_use",
        "env_id": env_id,
        "cwd": "/workspace"
    }
})

# Examine the response
print(f"Risk Level: {plan['risk_assessment']['risk_level']}")
print(f"Scope: {plan['risk_assessment']['scope']}")
print(f"Command to run: {plan['instructions']['command']}")
```

#### 4. Execution Phase (Container)

Execute the transformation in the isolated environment:

```python
# Run the grit command in container
result = await client.call_tool("environment_run_cmd", {
    "env_id": env_id,
    "command": plan["instructions"]["command"],
    "working_dir": plan["instructions"]["working_dir"]
})

# Review the diff
diff = await client.call_tool("environment_diff", {
    "env_id": env_id
})
```

#### 5. Review & Land Phase (Container → Host)

After reviewing changes, apply them to the host:

```python
# Option A: Merge with git history
await client.call_tool("environment_merge", {
    "env_id": env_id
})

# Option B: Apply changes without git history
await client.call_tool("environment_apply", {
    "env_id": env_id
})
```

### Practical Example: Upgrading React Components

Here's a complete example of using gritql-mcp with Container Use to safely upgrade React class components to hooks:

```python
async def upgrade_react_components(client):
    # 1. Check what will be changed (host mode)
    preview = await client.call_tool("code.find", {
        "gritql": "class_component($name) where { $name <: r'.*Component' }",
        "paths": ["src/"]
    })
    print(f"Found {len(preview['output'].splitlines())} components to upgrade")

    # 2. Create isolated environment
    env = await client.call_tool("environment_create", {
        "base_image": "node:20"
    })
    env_id = env["env_id"]

    # 3. Copy code and install dependencies
    await client.call_tool("environment_run_cmd", {
        "env_id": env_id,
        "command": "cp -r /host/project /workspace && cd /workspace && npm install"
    })

    # 4. Get transformation plan with risk assessment
    plan = await client.call_tool("code.apply", {
        "patternName": "react_class_to_hooks",
        "execution_target": {
            "type": "container_use",
            "env_id": env_id,
            "cwd": "/workspace"
        }
    })

    # 5. Check risk and get user confirmation if high-risk
    if plan["risk_assessment"]["risk_level"] == "high":
        print("⚠️ High-risk transformation detected!")
        print(f"Scope: {plan['risk_assessment']['scope']}")
        if not confirm("Proceed with transformation?"):
            return

    # 6. Execute transformation
    await client.call_tool("environment_run_cmd", {
        "env_id": env_id,
        "command": plan["instructions"]["command"],
        "working_dir": plan["instructions"]["working_dir"]
    })

    # 7. Run tests in container
    test_result = await client.call_tool("environment_run_cmd", {
        "env_id": env_id,
        "command": "npm test",
        "working_dir": "/workspace"
    })

    # 8. Review and land changes if tests pass
    if "failed" not in test_result["output"].lower():
        diff = await client.call_tool("environment_diff", {"env_id": env_id})
        print(f"Changes:\n{diff['output']}")

        if confirm("Apply changes to host?"):
            await client.call_tool("environment_apply", {"env_id": env_id})
            print("✅ Changes applied successfully")
    else:
        print("❌ Tests failed, changes not applied")
```

### Risk Assessment Levels

The gritql-mcp server provides risk metadata to help agents make informed decisions:

- **Low Risk**: Targeted changes to specific files
- **Medium Risk**: Refactoring operations (rename, move)
- **High Risk**: Repository-wide changes, destructive operations, API/interface changes

### Best Practices

1. **Always dry-run first**: Use `code.dry_run` before `code.apply` to preview changes
2. **Check risk levels**: Implement confirmation prompts for high-risk operations
3. **Test in container**: Run test suites after transformations before landing
4. **Incremental changes**: Apply patterns to specific paths rather than entire repositories
5. **Version control**: Use Container Use's merge option to preserve git history

## Development and Quality Assurance

This project is equipped with a suite of tools to ensure code quality and correctness.

### Installing Development Dependencies

To install the tools needed for testing and linting, run:
```bash
uv pip install -e .[dev]
```

### Running Tests

The project uses `pytest` for unit and integration testing. The test suite includes a full simulation of an MCP host to validate the server's behavior.
```bash
pytest
```

### Linting and Formatting

We use `ruff` for high-performance linting and code formatting.

-   **Check for linting errors:** `ruff check .`
-   **Automatically fix errors:** `ruff check --fix .`
-   **Check formatting:** `ruff format --check .`
-   **Reformat code:** `ruff format .`

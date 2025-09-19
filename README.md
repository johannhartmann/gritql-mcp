# GritQL MCP Server

This project implements a local-only Python [FastMCP](https://gofastmcp.com/) server that exposes the capabilities of the [GritQL engine](https://docs.grit.io/) to MCP-compatible clients like the [Codex CLI](https://github.com/openai/codex).

The server allows you to leverage GritQL for code searching and rewriting directly from your development environment, without relying on any cloud services or AI. All operations are performed locally.

## Features

The server exposes the following tools to the client:

-   `library.search_patterns`: Search the local Grit pattern library for patterns and workflows.
-   `patterns.describe`: Get detailed metadata for a specific pattern.
-   `gritql.generate`: Deterministically generate a GritQL query from a natural language problem description (local-only, no AI).
-   `code.find`: Find code in your workspace that matches a GritQL query or a named pattern.
-   `code.dry_run`: See a summary of the changes a rewrite pattern would make without applying them.
-   `code.apply`: Apply a GritQL rewrite directly to your codebase.

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python** (3.8 or higher)
2.  **uv**: Follow the official installation instructions at [astral.sh/uv](https://astral.sh/uv).
    ```bash
    # Recommended installation method
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
3.  **Grit CLI**: Follow the official installation instructions at [docs.grit.io/cli/quickstart](https://docs.grit.io/cli/quickstart).
    ```bash
    # Using npm
    npm install --location=global @getgrit/cli
    # Or using the install script
    curl -fsSL https://docs.grit.io/install | bash
    ```
4.  **An MCP-compatible client** (e.g., Gemini CLI, Codex CLI).

## Installation

1.  **Clone the repository** (or download the source code):
    ```bash
    git clone <repository-url>
    cd gritql-mcp
    ```

2.  **Install the Python dependencies**:
    This project uses `uv` for package management.
    ```bash
    # Create and activate a virtual environment
    uv venv
    source .venv/bin/activate

    # Install the package in editable mode
    uv pip install -e .
    ```

## Integrations

This server uses the Model Context Protocol (MCP) to expose its tools.

### Gemini CLI

To make the server available to the Gemini CLI, you need to add it to your Gemini configuration file.

1.  Locate or create the config file at `~/.gemini/settings.json`.

2.  Add the following to the `mcp_servers` list in the file, adjusting the paths as necessary:

    ```json
    {
      "command": "python",
      "args": ["-m", "server.main"],
      "name": "gritql"
    }
    ```

### OpenAI Codex and Claude

To integrate with clients that use OpenAI's or Anthropic's function calling/tool use APIs, you would need to create a translation layer. This layer would:
1.  Define the tools in the format required by the specific API (e.g., JSON schema for OpenAI).
2.  Receive the function call request from the model.
3.  Translate the request into an MCP call to this server.
4.  Receive the MCP response and translate it back into the format expected by the model's API.

This project does not include this translation layer out of the box.

## Usage

Once configured, your MCP client will automatically start and connect to the server. You can then invoke the tools by describing what you want to do in a natural way.

**Example (with Gemini CLI):**

1.  Navigate to a directory within your allowed workspace.
2.  Run the Gemini CLI:
    ```bash
    gemini
    ```
3.  Give it a prompt that triggers one of the tools:
    > "Using the gritql tool, find all functions named 'my_function' in the current directory."

The CLI will identify the appropriate tool (`code.find`), call the server, and display the results.

## Development and Quality Assurance

This project is equipped with a suite of tools to ensure code quality and correctness.

### Installing Development Dependencies

To install the tools needed for testing and linting, run:
```bash
uv pip install -e .[dev]
```

### Running Tests

The project uses `pytest` for unit and integration testing. To run the test suite:
```bash
pytest
```

### Linting and Formatting

We use `ruff` for high-performance linting and code formatting.

-   **To check for linting errors:**
    ```bash
    ruff check .
    ```
-   **To automatically fix linting errors:**
    ```bash
    ruff check --fix .
    ```
-   **To check for formatting issues:**
    ```bash
    ruff format --check .
    ```
-   **To reformat the code:**
    ```bash
    ruff format .
    ```

### CI Check Simulation

To run all the checks that a Continuous Integration (CI) pipeline would, execute the following commands in order:

```bash
# 1. Check formatting
ruff format --check .

# 2. Check for linting errors
ruff check .

# 3. Run the test suite
pytest
```
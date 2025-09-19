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

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python** (3.8 or higher)
2.  **uv**: Follow the official installation instructions at [astral.sh/uv](https://astral.sh/uv).
3.  **Grit CLI**: Follow the official installation instructions at [docs.grit.io/cli/quickstart](https://docs.grit.io/cli/quickstart).
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

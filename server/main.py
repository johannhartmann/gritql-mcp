from server.mcp_instance import mcp

# Import handlers to register the tools via decorators
from server.handlers import apply, dry_run, find, generate, library


def main():
    """
    The main entrypoint for the GritQL MCP server.
    """
    mcp.run()


if __name__ == "__main__":
    main()
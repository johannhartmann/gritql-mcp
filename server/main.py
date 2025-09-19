# Import handlers to register the tools via decorators
from server.handlers import apply
from server.handlers import dry_run
from server.handlers import find
from server.handlers import generate
from server.handlers import library
from server.mcp_instance import mcp


def main():
    """
    The main entrypoint for the GritQL MCP server.
    """
    mcp.run()


if __name__ == "__main__":
    main()

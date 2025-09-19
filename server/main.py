# Import handlers to register the tools via decorators
from server.mcp_instance import mcp


def main():
    """
    The main entrypoint for the GritQL MCP server.
    """
    mcp.run()


if __name__ == "__main__":
    main()

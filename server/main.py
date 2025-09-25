# Import handlers to register the tools via decorators
# These imports are needed to register the tools, even though they're not directly used
from server.handlers import (
    apply,  # noqa: F401
    dry_run,  # noqa: F401
    find,  # noqa: F401
    generate,  # noqa: F401
    library,  # noqa: F401
)
from server.mcp_instance import mcp


def main():
    """
    The main entrypoint for the GritQL MCP server.
    """
    mcp.run()


if __name__ == "__main__":
    main()

import fastmcp.server as mcp

from server.handlers import apply, dry_run, find, generate, library


def main():
    """
    The main entrypoint for the GritQL MCP server.
    """
    server = mcp.Server()
    server.register_tool("library.search_patterns", library.search_patterns)
    server.register_tool("patterns.describe", library.describe_pattern)
    server.register_tool("gritql.generate", generate.generate_gritql)
    server.register_tool("code.find", find.find_code)
    server.register_tool("code.dry_run", dry_run.dry_run_code)
    server.register_tool("code.apply", apply.apply_code)
    server.run()


if __name__ == "__main__":
    main()

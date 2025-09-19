import json
import os
import subprocess

from server.mcp_instance import mcp


def get_grit_cli_path():
    """Returns the path to the grit CLI executable."""
    return os.environ.get("GRIT_CLI_PATH", "grit")

def parse_list_output(output: str) -> list[dict]:
    """Parses the JSON output of `grit list` and `grit patterns list`."""
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return []

@mcp.tool("library.search_patterns")
def search_patterns(query: str, language: str, source: str, limit: int):
    """
    Search local library for patterns/workflows.
    """
    grit_cmd = get_grit_cli_path()

    # Call grit patterns list
    patterns_cmd = [grit_cmd, "patterns", "list"]
    if language:
        patterns_cmd.extend(["--language", language])
    if source != "all":
        patterns_cmd.extend(["--source", source])

    patterns_process = subprocess.run(patterns_cmd, capture_output=True, text=True)
    if patterns_process.returncode != 0:
        return {"error": patterns_process.stderr}

    patterns = parse_list_output(patterns_process.stdout)

    # Call grit list
    list_cmd = [grit_cmd, "list"]
    if language:
        list_cmd.extend(["--language", language])
    if source != "all":
        list_cmd.extend(["--source", source])

    list_process = subprocess.run(list_cmd, capture_output=True, text=True)
    if list_process.returncode != 0:
        return {"error": list_process.stderr}

    applyables = parse_list_output(list_process.stdout)

    # Combine and filter results
    all_items = patterns + applyables

    # A real implementation would filter by query here

    return {"items": json.dumps(all_items[:limit])}


@mcp.tool("patterns.describe")
def describe_pattern(name: str):
    """
    Return canonical metadata for a single pattern.
    """
    grit_cmd = get_grit_cli_path()
    cmd = [grit_cmd, "patterns", "describe", "--", name]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        return {"error": process.stderr}

    # Since there's no JSON output, we'll return the raw description text
    return {"description": process.stdout}

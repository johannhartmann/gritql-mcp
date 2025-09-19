import subprocess
import os

from server.mcp_instance import mcp
from server.policy import gating

def get_grit_cli_path():
    """Returns the path to the grit CLI executable."""
    return os.environ.get("GRIT_CLI_PATH", "grit")

@mcp.tool("code.find")
def find_code(
    gritql: str = None,
    patternName: str = None,
    language: str = None,
    paths: list[str] = None,
):
    """
    Find matches in the workspace (no writes).
    """
    if not gritql and not patternName:
        return {"error": "Either gritql or patternName is required."}

    # Policy enforcement
    if language and not gating.is_allowed_language(language):
        return {"error": f"Language is not allowed: {language}"}

    grit_cmd = get_grit_cli_path()
    pattern = gritql if gritql else patternName
    # The `check` command is more appropriate for finding matches without applying them.
    # It is also more likely to have a structured output format in the future.
    cmd = [grit_cmd, "check", pattern]

    if language:
        cmd.extend(["--language", language])
    
    # Add -- to prevent parameter injection
    if paths:
        cmd.append("--")
        cmd.extend(paths)

    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        return {"error": process.stderr}

    # Since there's no JSON output, return the raw stdout
    return {"output": process.stdout}

import subprocess
import os

from server.mcp_instance import mcp
from server.policy import gating

def get_grit_cli_path():
    """Returns the path to the grit CLI executable."""
    return os.environ.get("GRIT_CLI_PATH", "grit")

@mcp.tool("code.dry_run")
def dry_run_code(
    gritql: str = None,
    patternName: str = None,
    language: str = None,
    paths: list[str] = None,
):
    """
    Summarize the impact of a rewrite without diffs.
    """
    if not gritql and not patternName:
        return {"error": "Either gritql or patternName is required."}

    # Policy enforcement
    if language and not gating.is_allowed_language(language):
        return {"error": f"Language is not allowed: {language}"}

    grit_cmd = get_grit_cli_path()
    pattern = gritql if gritql else patternName
    cmd = [grit_cmd, "apply", pattern, "--dry-run"]

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

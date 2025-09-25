import os
import subprocess
from typing import Any, Dict, Optional

from server.execution_mode import (
    build_container_command,
    estimate_impact,
    execute_in_container,
    format_container_response,
    parse_execution_target,
)
from server.mcp_instance import mcp
from server.policy import gating


def get_grit_cli_path():
    """Returns the path to the grit CLI executable."""
    return os.environ.get("GRIT_CLI_PATH", "grit")


@mcp.tool("code.dry_run")
def dry_run_code(
    gritql: Optional[str] = None,
    patternName: Optional[str] = None,
    language: Optional[str] = None,
    paths: Optional[list[str]] = None,
    execution_target: Optional[Dict[str, Any]] = None,
):
    """
    Summarize the impact of a rewrite without diffs.

    Args:
        gritql: GritQL pattern to apply
        patternName: Name of predefined pattern to apply
        language: Target language
        paths: Specific paths to target
        execution_target: Execution mode configuration
            - {"type": "host"}: Execute directly on host (default)
            - {"type": "container_use", "env_id": "<id>", "cwd": "<path>"}:
              Return command for Container Use execution
    """
    if not gritql and not patternName:
        return {"error": "Either gritql or patternName is required."}

    # Policy enforcement
    if language and not gating.is_allowed_language(language):
        return {"error": f"Language is not allowed: {language}"}

    pattern = gritql if gritql else patternName
    if pattern is None:  # This should never happen due to earlier validation
        return {"error": "No pattern specified"}

    # Parse execution mode
    try:
        exec_mode = parse_execution_target(execution_target)
    except ValueError as e:
        return {"error": str(e)}

    # Container mode: execute inside container
    if exec_mode["type"] == "container_use":
        # Build command and estimate impact
        command_spec = build_container_command(
            pattern=pattern,
            dry_run=True,  # This is a dry run
            language=language,
            paths=paths,
            cwd=exec_mode["cwd"],
        )
        risk_metadata = estimate_impact(pattern, language, paths)

        # Execute the command inside the container
        returncode, stdout, stderr = execute_in_container(
            env_id=exec_mode["env_id"],
            command=command_spec["command"],
            working_dir=command_spec["working_dir"],
        )

        # Format and return the execution result
        execution_result = {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

        return format_container_response(
            execution_result=execution_result,
            risk_metadata=risk_metadata,
            env_id=exec_mode["env_id"],
            operation="dry_run",
        )

    # Host mode: execute directly (existing behavior)
    grit_cmd = get_grit_cli_path()
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

"""
Execution mode support for Container Use integration.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import docker
from docker.errors import APIError, ContainerError, NotFound


def parse_execution_target(
    execution_target: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Parse and validate execution_target parameter.

    Args:
        execution_target: Optional dict with execution mode configuration

    Returns:
        Parsed execution mode configuration
    """
    if not execution_target:
        return {"type": "host"}

    mode_type = execution_target.get("type", "host")

    if mode_type == "host":
        return {"type": "host"}
    elif mode_type == "container_use":
        env_id = execution_target.get("env_id")
        if not env_id:
            raise ValueError("container_use mode requires env_id")
        return {
            "type": "container_use",
            "env_id": env_id,
            "cwd": execution_target.get("cwd", "."),
        }
    else:
        raise ValueError(f"Unknown execution target type: {mode_type}")


def estimate_impact(
    pattern: str, language: Optional[str] = None, paths: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Estimate the risk and impact of applying a GritQL pattern.

    Args:
        pattern: GritQL pattern or pattern name
        language: Target language
        paths: Specific paths to target

    Returns:
        Risk metadata dictionary
    """
    risk_metadata = {
        "pattern": pattern,
        "scope": "unknown",
        "risk_level": "medium",
        "cross_module": False,
    }

    # If specific paths provided, scope is limited
    if paths:
        risk_metadata["scope"] = "targeted"
        risk_metadata["targeted_paths"] = paths
    else:
        risk_metadata["scope"] = "repository-wide"
        risk_metadata["cross_module"] = True

    # Language-specific risk assessment
    if language:
        risk_metadata["language"] = language
        # System-level languages carry higher risk
        if language in ["rust", "c", "cpp", "go"]:
            risk_metadata["risk_level"] = "high"

    # Pattern-based risk assessment (basic heuristics)
    if pattern:
        pattern_lower = pattern.lower()
        # High-risk patterns
        if any(
            keyword in pattern_lower
            for keyword in ["delete", "remove", "drop", "truncate"]
        ):
            risk_metadata["risk_level"] = "high"
            risk_metadata["destructive"] = True
        # API/interface changes
        elif any(
            keyword in pattern_lower
            for keyword in ["api", "interface", "public", "export"]
        ):
            risk_metadata["risk_level"] = "high"
            risk_metadata["cross_module"] = True
        # Refactoring patterns
        elif any(
            keyword in pattern_lower for keyword in ["rename", "refactor", "move"]
        ):
            risk_metadata["risk_level"] = "medium"

    return risk_metadata


def build_container_command(
    pattern: str,
    dry_run: bool = False,
    language: Optional[str] = None,
    paths: Optional[List[str]] = None,
    cwd: str = ".",
) -> Dict[str, Any]:
    """
    Build command specification for Container Use execution.

    Args:
        pattern: GritQL pattern or pattern name
        dry_run: Whether this is a dry run
        language: Target language
        paths: Specific paths to target
        cwd: Working directory within container

    Returns:
        Command specification for Container Use
    """
    # Build the grit command
    cmd_parts = ["grit", "apply", pattern]

    if dry_run:
        cmd_parts.append("--dry-run")

    if language:
        cmd_parts.extend(["--language", language])

    # Add paths with separator
    if paths:
        cmd_parts.append("--")
        cmd_parts.extend(paths)

    return {
        "command": " ".join(cmd_parts),
        "working_dir": cwd,
        "operation": "dry_run" if dry_run else "apply",
    }


def execute_in_container(
    env_id: str,
    command: str,
    working_dir: str = "/workspace",
) -> Tuple[int, str, str]:
    """
    Execute a command inside a Container Use environment using Docker SDK.

    Args:
        env_id: Container environment ID
        command: Command to execute
        working_dir: Working directory inside container

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    # Container Use environments are Docker containers with specific naming
    # The container name follows the pattern: container-use-env-{env_id}
    container_name = f"container-use-env-{env_id}"

    try:
        # Connect to Docker daemon
        client = docker.from_env()

        # Get the container
        try:
            container = client.containers.get(container_name)
        except NotFound:
            return (
                1,
                "",
                f"Container {container_name} not found. "
                f"Ensure the Container Use environment exists.",
            )

        # Check if container is running
        if container.status != "running":
            return (
                1,
                "",
                f"Container {container_name} is not running "
                f"(status: {container.status})",
            )

        # Execute command inside container
        # Note: exec_run returns ExecResult with exit_code and output attributes
        result = container.exec_run(
            cmd=["sh", "-c", command],
            workdir=working_dir,
            demux=True,  # Separate stdout and stderr
            tty=False,
        )

        # Handle the result
        exit_code = result.exit_code

        # demux=True returns tuple (stdout, stderr) or None if stream empty
        if result.output:
            stdout = result.output[0].decode("utf-8") if result.output[0] else ""
            stderr = result.output[1].decode("utf-8") if result.output[1] else ""
        else:
            stdout = ""
            stderr = ""

        return exit_code, stdout, stderr

    except APIError as e:
        # Docker API errors (connection issues, daemon problems)
        logging.error(f"Docker API error: {e}")
        error_msg = e.explanation if hasattr(e, "explanation") else str(e)
        return (
            1,
            "",
            f"Docker API error: {error_msg}",
        )
    except ContainerError as e:
        # Container-specific errors during execution
        logging.error(f"Container execution error: {e}")
        return 1, "", f"Container execution failed: {str(e)}"
    except Exception as e:
        # Catch-all for unexpected errors
        logging.error(f"Unexpected error executing in container: {e}")
        return 1, "", f"Failed to execute in container: {str(e)}"


def format_container_response(
    execution_result: Dict[str, Any],
    risk_metadata: Dict[str, Any],
    env_id: str,
    operation: str,
) -> Dict[str, Any]:
    """
    Format response for container mode execution.

    Args:
        execution_result: Result from container execution
        risk_metadata: Risk assessment metadata
        env_id: Container environment ID
        operation: Type of operation (apply/dry_run)

    Returns:
        Formatted response for agent consumption
    """
    success = execution_result.get("returncode", 1) == 0

    response = {
        "execution_mode": "container_use",
        "env_id": env_id,
        "operation": operation,
        "success": success,
        "risk_assessment": risk_metadata,
    }

    if success:
        response["output"] = execution_result.get("stdout", "")
        response["message"] = f"Successfully executed {operation} in container {env_id}"
        response["next_steps"] = {
            "review": f"Use 'container-use diff {env_id}' to review changes",
            "test": "Run tests in container to verify changes",
            "land": (
                f"Use 'container-use merge {env_id}' or "
                f"'container-use apply {env_id}' to accept changes"
            ),
        }
    else:
        response["error"] = execution_result.get("stderr", "Unknown error")
        response["message"] = f"Failed to execute {operation} in container"
        response["troubleshooting"] = {
            "check_container": f"Verify container {env_id} is running",
            "check_grit": "Ensure grit CLI is installed in the container",
            "check_path": "Verify working directory exists in container",
        }

    return response

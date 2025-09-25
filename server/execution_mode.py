"""
Execution mode support for Container Use integration.
"""

from typing import Any, Dict, List, Optional


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


def format_container_response(
    command_spec: Dict[str, Any], risk_metadata: Dict[str, Any], env_id: str
) -> Dict[str, Any]:
    """
    Format response for container mode execution.

    Args:
        command_spec: Command specification
        risk_metadata: Risk assessment metadata
        env_id: Container environment ID

    Returns:
        Formatted response for agent consumption
    """
    return {
        "execution_mode": "container_use",
        "env_id": env_id,
        "instructions": {
            "command": command_spec["command"],
            "working_dir": command_spec["working_dir"],
            "expected_artifacts": [
                "stdout output from grit command",
                f"repository diff via: container-use diff {env_id}",
            ],
            "operation": command_spec["operation"],
        },
        "risk_assessment": risk_metadata,
        "next_steps": {
            "execute": f"Use environment_run_cmd to run: {command_spec['command']}",
            "review": f"Use 'container-use diff {env_id}' to review changes",
            "land": (
                f"Use 'container-use merge {env_id}' or "
                f"'container-use apply {env_id}' to accept changes"
            ),
        },
    }

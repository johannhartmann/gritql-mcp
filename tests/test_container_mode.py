"""
Tests for Container Use integration mode.
"""

import os
import sys

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from server.execution_mode import (
    build_container_command,
    estimate_impact,
    format_container_response,
    parse_execution_target,
)

# Note: The decorated tool functions can't be called directly in tests
# We'll test the underlying functions instead


def test_parse_execution_target_host_mode():
    """Test parsing host mode execution target."""
    # Default to host mode
    assert parse_execution_target(None) == {"type": "host"}
    assert parse_execution_target({"type": "host"}) == {"type": "host"}


def test_parse_execution_target_container_mode():
    """Test parsing container mode execution target."""
    target = {"type": "container_use", "env_id": "env123", "cwd": "/app"}
    result = parse_execution_target(target)
    assert result == {"type": "container_use", "env_id": "env123", "cwd": "/app"}

    # Default cwd
    target = {"type": "container_use", "env_id": "env456"}
    result = parse_execution_target(target)
    assert result == {"type": "container_use", "env_id": "env456", "cwd": "."}


def test_parse_execution_target_invalid():
    """Test parsing invalid execution targets."""
    with pytest.raises(ValueError, match="Unknown execution target type"):
        parse_execution_target({"type": "invalid"})

    with pytest.raises(ValueError, match="container_use mode requires env_id"):
        parse_execution_target({"type": "container_use"})


def test_estimate_impact_with_paths():
    """Test risk estimation with specific paths."""
    risk = estimate_impact("rename_function", paths=["src/main.py"])
    assert risk["scope"] == "targeted"
    assert risk["risk_level"] == "medium"  # rename is medium risk
    assert risk["targeted_paths"] == ["src/main.py"]


def test_estimate_impact_repository_wide():
    """Test risk estimation for repository-wide changes."""
    risk = estimate_impact("rename_function")
    assert risk["scope"] == "repository-wide"
    assert risk["risk_level"] == "medium"  # rename is medium risk
    assert risk["cross_module"] is True


def test_estimate_impact_destructive_pattern():
    """Test risk estimation for destructive patterns."""
    risk = estimate_impact("delete_unused_imports")
    assert risk["risk_level"] == "high"
    assert risk.get("destructive") is True


def test_estimate_impact_api_changes():
    """Test risk estimation for API changes."""
    risk = estimate_impact("update_public_api")
    assert risk["risk_level"] == "high"
    assert risk["cross_module"] is True


def test_build_container_command_apply():
    """Test building container command for apply."""
    cmd = build_container_command(
        pattern="rename_function",
        dry_run=False,
        language="python",
        paths=["src/main.py", "src/utils.py"],
        cwd="/app/project",
    )
    assert (
        cmd["command"]
        == "grit apply rename_function --language python -- src/main.py src/utils.py"
    )
    assert cmd["working_dir"] == "/app/project"
    assert cmd["operation"] == "apply"


def test_build_container_command_dry_run():
    """Test building container command for dry run."""
    cmd = build_container_command(
        pattern="fix_imports", dry_run=True, language="javascript"
    )
    assert cmd["command"] == "grit apply fix_imports --dry-run --language javascript"
    assert cmd["working_dir"] == "."
    assert cmd["operation"] == "dry_run"


def test_format_container_response():
    """Test formatting container response."""
    command_spec = {
        "command": "grit apply pattern",
        "working_dir": "/app",
        "operation": "apply",
    }
    risk_metadata = {"risk_level": "medium", "scope": "targeted"}
    response = format_container_response(command_spec, risk_metadata, "env789")

    assert response["execution_mode"] == "container_use"
    assert response["env_id"] == "env789"
    assert response["instructions"]["command"] == "grit apply pattern"
    assert response["instructions"]["working_dir"] == "/app"
    assert response["risk_assessment"] == risk_metadata
    assert "execute" in response["next_steps"]
    assert "review" in response["next_steps"]
    assert "land" in response["next_steps"]


def test_container_mode_response_format():
    """Test the format of container mode response."""
    # Test building container command and response for apply
    command_spec = build_container_command(
        pattern="test_pattern",
        dry_run=False,
        language="python",
        paths=["test.py"],
        cwd="/workspace",
    )
    risk_metadata = estimate_impact("test_pattern", "python", ["test.py"])
    response = format_container_response(command_spec, risk_metadata, "test_env")

    assert response["execution_mode"] == "container_use"
    assert response["env_id"] == "test_env"
    assert "grit apply" in response["instructions"]["command"]
    assert response["instructions"]["working_dir"] == "/workspace"
    assert response["instructions"]["operation"] == "apply"
    assert "risk_assessment" in response


def test_dry_run_container_mode_response_format():
    """Test the format of container mode dry run response."""
    # Test building container command and response for dry run
    command_spec = build_container_command(
        pattern="standard_pattern",
        dry_run=True,
        language="python",
        paths=["test.py"],
        cwd=".",
    )
    risk_metadata = estimate_impact("standard_pattern", "python", ["test.py"])
    response = format_container_response(command_spec, risk_metadata, "dry_env")

    assert response["execution_mode"] == "container_use"
    assert response["env_id"] == "dry_env"
    assert "--dry-run" in response["instructions"]["command"]
    assert response["instructions"]["operation"] == "dry_run"
    assert response["risk_assessment"]["scope"] == "targeted"

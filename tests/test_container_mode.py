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
    execute_in_container,
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


def test_format_container_response_success():
    """Test formatting successful container response."""
    execution_result = {
        "returncode": 0,
        "stdout": "Applied pattern successfully",
        "stderr": "",
    }
    risk_metadata = {"risk_level": "medium", "scope": "targeted"}
    response = format_container_response(
        execution_result, risk_metadata, "env789", "apply"
    )

    assert response["execution_mode"] == "container_use"
    assert response["env_id"] == "env789"
    assert response["operation"] == "apply"
    assert response["success"] is True
    assert response["output"] == "Applied pattern successfully"
    assert response["risk_assessment"] == risk_metadata
    assert "review" in response["next_steps"]
    assert "test" in response["next_steps"]
    assert "land" in response["next_steps"]


def test_format_container_response_failure():
    """Test formatting failed container response."""
    execution_result = {
        "returncode": 1,
        "stdout": "",
        "stderr": "Pattern not found",
    }
    risk_metadata = {"risk_level": "low", "scope": "targeted"}
    response = format_container_response(
        execution_result, risk_metadata, "env_fail", "dry_run"
    )

    assert response["execution_mode"] == "container_use"
    assert response["env_id"] == "env_fail"
    assert response["operation"] == "dry_run"
    assert response["success"] is False
    assert response["error"] == "Pattern not found"
    assert "troubleshooting" in response
    assert "check_container" in response["troubleshooting"]
    assert "check_grit" in response["troubleshooting"]


def test_execute_in_container_success(mocker):
    """Test successful command execution in container using docker-py."""
    # Mock docker client and container
    mock_docker = mocker.patch("docker.from_env")
    mock_client = mocker.MagicMock()
    mock_docker.return_value = mock_client

    # Mock container
    mock_container = mocker.MagicMock()
    mock_container.status = "running"
    mock_client.containers.get.return_value = mock_container

    # Mock exec_run result
    mock_result = mocker.MagicMock()
    mock_result.exit_code = 0
    mock_result.output = (b"Command output", b"")
    mock_container.exec_run.return_value = mock_result

    returncode, stdout, stderr = execute_in_container(
        env_id="test123", command="grit apply pattern", working_dir="/workspace"
    )

    assert returncode == 0
    assert stdout == "Command output"
    assert stderr == ""

    # Verify container was fetched and command was executed
    mock_client.containers.get.assert_called_once_with("container-use-env-test123")
    mock_container.exec_run.assert_called_once_with(
        cmd=["sh", "-c", "grit apply pattern"],
        workdir="/workspace",
        demux=True,
        tty=False,
    )


def test_execute_in_container_not_found(mocker):
    """Test handling when container doesn't exist."""
    # Mock docker client to raise NotFound
    mock_docker = mocker.patch("docker.from_env")
    mock_client = mocker.MagicMock()
    mock_docker.return_value = mock_client

    from docker.errors import NotFound

    mock_client.containers.get.side_effect = NotFound("Container not found")

    returncode, stdout, stderr = execute_in_container(
        env_id="missing", command="grit apply pattern"
    )

    assert returncode == 1
    assert stdout == ""
    assert "not found" in stderr
    assert "Container Use environment exists" in stderr


def test_execute_in_container_not_running(mocker):
    """Test handling when container is not running."""
    # Mock docker client and container
    mock_docker = mocker.patch("docker.from_env")
    mock_client = mocker.MagicMock()
    mock_docker.return_value = mock_client

    # Mock container that's not running
    mock_container = mocker.MagicMock()
    mock_container.status = "exited"
    mock_client.containers.get.return_value = mock_container

    returncode, stdout, stderr = execute_in_container(
        env_id="stopped", command="grit apply pattern"
    )

    assert returncode == 1
    assert stdout == ""
    assert "not running" in stderr
    assert "status: exited" in stderr
